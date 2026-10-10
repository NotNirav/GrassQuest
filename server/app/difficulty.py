"""P(user completes quest) -> drives the XP multiplier.

Cold start: users with fewer than TABPFN_MIN_USER_ATTEMPTS attempts get a heuristic.
After that, TabPFN predicts from everyone's attempt history (real rows + rows marked synthetic=True).
"""
import logging
import time

import numpy as np
import sentry_sdk

from . import config, db, tabpfn_budget

log = logging.getLogger(__name__)

CATEGORIES = ["plants", "birds", "sky", "walking", "water", "textures", "social"]
RARITIES = ["common", "rare", "legendary", "boss"]
FEATURES = ["hour", "dow", "category", "rarity", "streak", "user_attempts", "user_pass_rate", "quest_pass_rate"]

RARITY_PRIOR = {"common": 0.8, "rare": 0.55, "legendary": 0.3, "boss": 0.4}
NIGHT_HOSTILE = {"birds", "plants", "textures", "water"}  # hard to photograph in the dark
NIGHT_FRIENDLY = {"sky"}

_model_cache = {"model": None, "fitted_at": 0.0, "rows": 0}
MODEL_TTL_S = 600


def user_stats(user_id: str) -> dict:
    rows = list(db.attempts.find({"user_id": user_id, "synthetic": {"$ne": True}}, {"outcome": 1}))
    n = len(rows)
    passed = sum(r["outcome"] == "pass" for r in rows)
    # Laplace-smoothed so a brand-new user isn't 0% or 100%
    return {"attempts": n, "pass_rate": (passed + 1) / (n + 2)}


def quest_pass_rates() -> dict:
    out = {}
    for row in db.attempts.aggregate([
        {"$group": {"_id": "$quest_id", "n": {"$sum": 1}, "p": {"$sum": {"$cond": [{"$eq": ["$outcome", "pass"]}, 1, 0]}}}}
    ]):
        out[row["_id"]] = (row["p"] + 1) / (row["n"] + 2)
    return out


def feature_row(quest: dict, hour: int, dow: int, streak: int, stats: dict, qrate: float) -> list[float]:
    return [
        hour, dow,
        CATEGORIES.index(quest["category"]) if quest["category"] in CATEGORIES else -1,
        RARITIES.index(quest["rarity"]),
        streak, stats["attempts"], stats["pass_rate"], qrate,
    ]


def heuristic(quest: dict, hour: int, stats: dict) -> float:
    p = RARITY_PRIOR[quest["rarity"]]
    night = hour >= 20 or hour < 6
    if night and quest["category"] in NIGHT_HOSTILE:
        p *= 0.5
    if night and quest["category"] in NIGHT_FRIENDLY:
        p = min(1.0, p * 1.15)
    # nudge towards the player's own track record
    p = 0.7 * p + 0.3 * stats["pass_rate"]
    return round(min(max(p, 0.05), 0.95), 3)


def _training_set():
    rows = list(db.attempts.find({"outcome": {"$in": ["pass", "fail", "skip"]}}))
    if len(rows) < 20:
        return None, None
    X = np.array([[r["features"][f] for f in FEATURES] for r in rows if "features" in r], dtype=float)
    y = np.array([1 if r["outcome"] == "pass" else 0 for r in rows if "features" in r])
    if len(set(y)) < 2:
        return None, None
    return X, y


def _fitted_model():
    if not config.TABPFN_TOKEN:
        return None
    if _model_cache["model"] and time.time() - _model_cache["fitted_at"] < MODEL_TTL_S:
        return _model_cache["model"]
    X, y = _training_set()
    if X is None:
        return None
    from tabpfn_client import TabPFNClassifier, set_access_token

    set_access_token(config.TABPFN_TOKEN)
    with sentry_sdk.start_span(op="tabpfn.fit", name="TabPFN fit") as span:
        model = TabPFNClassifier()
        model.fit(X, y)
        span.set_data("rows", len(y))
    _model_cache.update(model=model, fitted_at=time.time(), rows=len(y))
    return model


_pred_cache: dict[tuple, tuple[float, dict]] = {}
PRED_TTL_S = 1800


def _tabpfn_all(user_id: str, hour: int, dow: int, streak: int, stats: dict, qrates: dict) -> dict | None:
    """One TabPFN call scores every quest for this player; reused for 30 min or until their history changes."""
    key = (user_id, hour, dow, streak, stats["attempts"])
    hit = _pred_cache.get(key)
    if hit and time.time() - hit[0] < PRED_TTL_S:
        return hit[1]
    ok, why = tabpfn_budget.allow(user_id)
    if not ok:
        log.info("TabPFN skipped for %s: %s", user_id, why)
        return None
    model = _fitted_model()
    if model is None:
        return None
    pool = list(db.quests.find({}, {"embedding": 0}))
    X = np.array([feature_row(q, hour, dow, streak, stats, qrates.get(q["_id"], 0.5)) for q in pool], dtype=float)
    try:
        with sentry_sdk.start_span(op="tabpfn.predict", name="TabPFN predict_proba") as span:
            proba = model.predict_proba(X)[:, 1]
            span.set_data("quests", len(pool))
    except Exception as e:
        tabpfn_budget.on_error(e)
        raise
    tabpfn_budget.record(user_id)
    scores = {q["_id"]: round(float(min(max(p, 0.05), 0.95)), 3) for q, p in zip(pool, proba)}
    for k in [k for k in _pred_cache if k[0] == user_id]:  # one cached entry per player
        del _pred_cache[k]
    _pred_cache[key] = (time.time(), scores)
    return scores


def predict(user_id: str, quests: list[dict], hour: int, dow: int, streak: int) -> tuple[list[float], list[list[float]], str]:
    """Returns (probabilities, feature rows, source) where source is 'tabpfn' or 'heuristic'."""
    stats = user_stats(user_id)
    qrates = quest_pass_rates()
    feats = [feature_row(q, hour, dow, streak, stats, qrates.get(q["_id"], 0.5)) for q in quests]

    if stats["attempts"] >= config.TABPFN_MIN_USER_ATTEMPTS:
        try:
            scores = _tabpfn_all(user_id, hour, dow, streak, stats, qrates)
            if scores is not None and all(q["_id"] in scores for q in quests):
                return [scores[q["_id"]] for q in quests], feats, "tabpfn"
        except Exception:  # network/API trouble must never block a quest
            log.exception("TabPFN failed, falling back to heuristic")
    return [heuristic(q, hour, stats) for q in quests], feats, "heuristic"


def status() -> dict:
    return {
        "tabpfn_configured": bool(config.TABPFN_TOKEN),
        "min_user_attempts": config.TABPFN_MIN_USER_ATTEMPTS,
        "training_rows": db.attempts.count_documents({}),
        "synthetic_rows": db.attempts.count_documents({"synthetic": True}),
        "last_fit_rows": _model_cache["rows"],
        "budget": tabpfn_budget.status(),
    }
