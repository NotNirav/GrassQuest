"""Picks today's three quest choices from what's actually possible where the player is, right now.

  1. eligibility (code): nearby places, weather band, time of day, daylight, rain coming
  2. freshness: skip templates played in the last 3 days + near-duplicates of them (Atlas Vector Search over template embeddings)
  3. TabPFN scores the rest -> easy (highest odds), sweet spot (closest to 65%), stretch (hardest that's still realistic)
"""
import random
from datetime import datetime, timedelta, timezone

import numpy as np
import sentry_sdk

from . import db

DUPLICATE_THRESHOLD = 0.80
VECTOR_INDEX = "template_embedding_index"
SWEET_SPOT = 0.65
MAX_CANDIDATES = 45
PUBLIC = {"_id": 1, "id": 1, "template_id": 1, "title": 1, "cat": 1, "needs": 1, "effort": 1, "rarity": 1, "minutes": 1,
          "time": 1, "wet": 1, "rain": 1, "kind": 1, "proof": 1, "twist": 1}


# ---------- 1. eligibility ----------
def time_ok(q: dict, phase: str) -> bool:
    t = q["time"]
    if t == "any":
        return True
    if t == "day":
        return phase in ("morning", "day", "golden")
    return t == phase


def weather_ok(q: dict, wx: dict) -> bool:
    band = wx["band"]
    if band == "severe":
        return q["rain"]
    if q["rain"]:
        return band in ("rain", "drizzle")  # rain checks only appear when the weather is actually bad
    if band == "rain":
        return q["wet"]
    if band == "drizzle":
        return q["wet"] or q["effort"] <= 2
    if band == "hot":
        return q["effort"] <= 3 and q["minutes"] <= 30
    if band == "cold":
        return q["minutes"] <= 40
    if wx.get("rain_soon_at") and not q["wet"]:
        return q["minutes"] <= 40
    return True


def sky_ok(q: dict, wx: dict) -> bool:
    if q["template_id"] in ("star", "moon-day", "sunset-high", "sunset-view", "sky-colors", "golden-tree", "long-shadow"):
        return wx["band"] in ("clear", "cloudy", "windy", "hot", "cold") and wx["code"] <= 2
    return True


def eligible(ctx: dict) -> list[dict]:
    features = set(ctx["features"])
    phase = ctx["sun"]["phase"]
    wx = ctx["weather"]
    pool = db.quests.find({}, PUBLIC)
    return [q for q in pool
            if set(q["needs"]) <= features and time_ok(q, phase) and weather_ok(q, wx) and sky_ok(q, wx)]


# ---------- 2. freshness ----------
def recent_templates(user_id: str, days: int = 3) -> list[str]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    cur = db.attempts.find({"user_id": user_id, "accepted": True, "created_at": {"$gte": since}}, {"template_id": 1}).sort("created_at", -1)
    return list(dict.fromkeys(a["template_id"] for a in cur if a.get("template_id")))


def _similar(embedding: list[float]) -> dict[str, float]:
    if db.USING_ATLAS:
        pipeline = [
            {"$vectorSearch": {"index": VECTOR_INDEX, "path": "embedding", "queryVector": embedding, "numCandidates": 60, "limit": 10}},
            {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
        ]
        return {d["_id"]: 2 * d["score"] - 1 for d in db.templates.aggregate(pipeline)}  # Atlas cosine score -> cosine
    q = np.array(embedding)
    out = {}
    for d in db.templates.find({}, {"embedding": 1}):
        v = np.array(d["embedding"])
        out[d["_id"]] = float(q @ v / (np.linalg.norm(q) * np.linalg.norm(v)))
    return out


def blocked_templates(user_id: str) -> tuple[set[str], list[str], list[str]]:
    recent = recent_templates(user_id)
    dupes = set()
    with sentry_sdk.start_span(op="db.vector_search", name="Template dedupe"):
        for tid in recent[:4]:
            t = db.templates.find_one({"_id": tid}, {"embedding": 1})
            if t and "embedding" in t:
                dupes |= {k for k, s in _similar(t["embedding"]).items() if s >= DUPLICATE_THRESHOLD and k != tid}
    return set(recent) | dupes, recent, sorted(dupes)


# ---------- 3. choose ----------
def candidates(user_id: str, pool: list[dict], exclude: list[str]) -> tuple[list[dict], dict]:
    blocked, recent, dupes = blocked_templates(user_id)
    fresh = [q for q in pool if q["template_id"] not in blocked and q["_id"] not in exclude]
    if len(fresh) < 6:  # played everything nearby recently: relax the dedupe
        fresh = [q for q in pool if q["template_id"] not in set(recent[:2]) and q["_id"] not in exclude] or pool
    # one quest per template keeps the shortlist varied; then cap it so a TabPFN call stays small
    random.shuffle(fresh)
    seen, varied = set(), []
    for q in fresh:
        if q["template_id"] not in seen:
            seen.add(q["template_id"])
            varied.append(q)
    return varied[:MAX_CANDIDATES], {"eligible": len(pool), "recent_templates": recent, "near_duplicates": dupes}


def three_choices(scored: list[tuple[dict, dict]]) -> list[tuple[str, dict, dict]]:
    """scored = [(quest, score)]. Returns [(slot, quest, score)] for easy / sweet / stretch."""
    if not scored:
        return []
    by_p = sorted(scored, key=lambda qs: qs[1]["p"], reverse=True)
    sweet = min(scored, key=lambda qs: abs(qs[1]["p"] - SWEET_SPOT) - 0.02 * qs[0]["effort"])
    rest = [qs for qs in by_p if qs[0]["_id"] != sweet[0]["_id"]]
    easy = rest[0] if rest else None
    realistic = [qs for qs in rest[1:] if qs[1]["p"] >= 0.15] or rest[1:]
    stretch = max(realistic, key=lambda qs: (qs[0]["effort"], -qs[1]["p"])) if realistic else None
    out = [("sweet", *sweet)]
    if easy:
        out.insert(0, ("easy", *easy))
    if stretch:
        out.append(("stretch", *stretch))
    return out
