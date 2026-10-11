"""TabPFN's two jobs:
  1. P(this player finishes this quest right now)  -> picks the three choices (easy / sweet spot / stretch) and scales XP
  2. Minutes it'll take (regressor)                 -> shown on every quest card

Trained on everyone's attempt history: real rows + rows marked synthetic=True (cold start, stated openly).
Every call goes through tabpfn_budget, which keeps us inside the free tier. If TabPFN is unavailable, a heuristic takes over.
"""
import logging
import time

import numpy as np
import sentry_sdk

from . import config, db, tabpfn_budget

log = logging.getLogger(__name__)

CATEGORIES = ["nature", "birds", "sky", "move", "explore", "water", "mindful", "photo", "social", "food", "rain"]
FEATURES = ["hour", "dow", "category", "effort", "minutes", "streak", "user_attempts", "user_pass_rate",
            "temp", "precip_mm", "wind", "minutes_to_sunset", "dist_m"]

MODEL_TTL_S = 600
PRED_TTL_S = 1800
_models = {"clf": None, "reg": None, "fitted_at": 0.0, "rows": 0, "reg_rows": 0}
_pred_cache: dict[tuple, tuple[float, dict]] = {}


def user_stats(user_id: str) -> dict:
    rows = list(db.attempts.find({"user_id": user_id, "outcome": {"$in": ["pass", "fail", "skip"]}}, {"outcome": 1}))
    n = len(rows)
    passed = sum(r["outcome"] == "pass" for r in rows)
    return {"attempts": n, "pass_rate": round((passed + 1) / (n + 2), 3)}  # Laplace-smoothed


def feature_row(q: dict, ctx: dict, streak: int, stats: dict, dist_m: int) -> list[float]:
    wx, sun = ctx["weather"], ctx["sun"]
    return [
        sun["local_hour"], sun["local_dow"],
        CATEGORIES.index(q["cat"]) if q["cat"] in CATEGORIES else -1,
        q["effort"], q["minutes"], streak, stats["attempts"], stats["pass_rate"],
        wx["temp"], wx["precip_mm"], wx["wind"], max(-300, min(600, sun["minutes_to_sunset"])), dist_m,
    ]


def heuristic(q: dict, ctx: dict, stats: dict, dist_m: int) -> float:
    p = {1: 0.88, 2: 0.75, 3: 0.58, 4: 0.42, 5: 0.28}[q["effort"]]
    band = ctx["weather"]["band"]
    if band in ("rain", "drizzle") and not q["wet"]:
        p *= 0.7
    if band in ("hot", "cold"):
        p *= 0.85
    p *= 1 - min(dist_m, 1500) / 6000  # every 1.5 km costs ~25%
    p = 0.75 * p + 0.25 * stats["pass_rate"]
    return round(min(max(p, 0.05), 0.95), 3)


def heuristic_minutes(q: dict, dist_m: int) -> int:
    return round(q["minutes"] + 2 * dist_m / 80)  # walking there and back at ~80 m/min


def _training():
    rows = list(db.attempts.find({"outcome": {"$in": ["pass", "fail", "skip"]}, "features.temp": {"$exists": True}},
                                 {"features": 1, "outcome": 1, "duration_min": 1}))
    if len(rows) < 30:
        return None
    X = np.array([[r["features"][f] for f in FEATURES] for r in rows], dtype=float)
    y = np.array([1 if r["outcome"] == "pass" else 0 for r in rows])
    timed = [(x, r["duration_min"]) for x, r in zip(X, rows) if r["outcome"] == "pass" and r.get("duration_min")]
    return X, y, timed


def _fit():
    if _models["clf"] is not None and time.time() - _models["fitted_at"] < MODEL_TTL_S:
        return True
    data = _training()
    if data is None or len(set(data[1])) < 2:
        return False
    from tabpfn_client import TabPFNClassifier, TabPFNRegressor, set_access_token

    set_access_token(config.TABPFN_TOKEN)
    X, y, timed = data
    with sentry_sdk.start_span(op="tabpfn.fit", name="TabPFN fit (fits are free)") as span:
        clf = TabPFNClassifier()
        clf.fit(X, y)
        reg = None
        if len(timed) >= 30:
            reg = TabPFNRegressor()
            reg.fit(np.array([t[0] for t in timed]), np.array([t[1] for t in timed], dtype=float))
        span.set_data("rows", len(y))
    _models.update(clf=clf, reg=reg, fitted_at=time.time(), rows=len(y), reg_rows=len(timed))
    return True


def score(user_id: str, quests: list[dict], ctx: dict, streak: int) -> dict:
    """Returns {quest_id: {"p", "minutes", "features", "source"}} for every candidate."""
    stats = user_stats(user_id)
    dists = {q["_id"]: (ctx["places"].get(q["needs"][0], {}).get("dist_m", 0) if q["needs"] else 0) for q in quests}
    feats = {q["_id"]: feature_row(q, ctx, streak, stats, dists[q["_id"]]) for q in quests}
    out = {q["_id"]: {"p": heuristic(q, ctx, stats, dists[q["_id"]]), "minutes": heuristic_minutes(q, dists[q["_id"]]),
                      "features": dict(zip(FEATURES, feats[q["_id"]])), "source": "heuristic"} for q in quests}

    if not config.TABPFN_TOKEN or stats["attempts"] < config.TABPFN_MIN_USER_ATTEMPTS:
        return out
    key = (user_id, tuple(ctx["cell"]), ctx["sun"]["local_hour"], ctx["weather"]["band"], streak, stats["attempts"])
    hit = _pred_cache.get(key)
    if hit and time.time() - hit[0] < PRED_TTL_S:
        # the cached call may predate new quests: keep the starter estimate for anything it didn't score
        return {qid: hit[1].get(qid, v) for qid, v in out.items()}
    ok, why = tabpfn_budget.allow(user_id, calls=2)
    if not ok:
        log.info("TabPFN skipped: %s", why)
        for v in out.values():
            v["source"] = f"heuristic ({why})"
        return out
    try:
        if not _fit():
            return out
        ids = [q["_id"] for q in quests]
        X = np.array([feats[i] for i in ids], dtype=float)
        with sentry_sdk.start_span(op="tabpfn.predict", name="TabPFN predict_proba") as span:
            proba = _models["clf"].predict_proba(X)[:, 1]
            span.set_data("candidates", len(ids))
        tabpfn_budget.record(user_id)
        minutes = None
        if _models["reg"] is not None:
            with sentry_sdk.start_span(op="tabpfn.predict", name="TabPFN regressor (minutes)"):
                minutes = _models["reg"].predict(X)
            tabpfn_budget.record(user_id)
        for k, i in enumerate(ids):
            out[i]["p"] = round(float(min(max(proba[k], 0.05), 0.95)), 3)
            if minutes is not None:
                out[i]["minutes"] = max(3, int(round(float(minutes[k]))))
            out[i]["source"] = "tabpfn"
    except Exception as e:
        tabpfn_budget.on_error(e)
        log.exception("TabPFN failed, using heuristic")
        return out
    for k in [k for k in _pred_cache if k[0] == user_id]:
        del _pred_cache[k]
    _pred_cache[key] = (time.time(), out)
    return out


def warm():
    """Fit both models ahead of time (fits cost no tokens)."""
    if config.TABPFN_TOKEN:
        try:
            _fit()
        except Exception:
            log.exception("TabPFN warm-up failed")


def status() -> dict:
    return {
        "tabpfn_configured": bool(config.TABPFN_TOKEN),
        "training_rows": db.attempts.count_documents({"features.temp": {"$exists": True}, "outcome": {"$in": ["pass", "fail", "skip"]}}),
        "synthetic_rows": db.attempts.count_documents({"synthetic": True}),
        "last_fit_rows": _models["rows"], "regressor_rows": _models["reg_rows"],
        "budget": tabpfn_budget.status(),
    }
