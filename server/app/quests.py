"""Picks the next quest: skip recent ones, drop near-duplicates (vector search), then weighted random by rarity."""
import random
from datetime import date, datetime, timedelta, timezone

import numpy as np
import sentry_sdk

from . import db

RARITY_WEIGHT = {"common": 60, "rare": 30, "legendary": 10}
DUPLICATE_THRESHOLD = 0.78  # cosine similarity above this counts as "basically the same quest"
VECTOR_INDEX = "quest_embedding_index"
PUBLIC_FIELDS = {"embedding": 0}


def recent_quest_ids(user_id: str, days: int = 3, limit: int = 20) -> list[str]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    cur = db.attempts.find({"user_id": user_id, "created_at": {"$gte": since}}, {"quest_id": 1}).sort("created_at", -1).limit(limit)
    return list(dict.fromkeys(a["quest_id"] for a in cur))


def _similar_ids_atlas(embedding: list[float]) -> dict[str, float]:
    pipeline = [
        {"$vectorSearch": {"index": VECTOR_INDEX, "path": "embedding", "queryVector": embedding, "numCandidates": 50, "limit": 8}},
        {"$project": {"_id": 1, "score": {"$meta": "vectorSearchScore"}}},
    ]
    # Atlas cosine score is (1 + cos) / 2; convert back to cosine
    return {d["_id"]: 2 * d["score"] - 1 for d in db.quests.aggregate(pipeline)}


def _similar_ids_local(embedding: list[float]) -> dict[str, float]:
    q = np.array(embedding)
    out = {}
    for d in db.quests.find({"embedding": {"$exists": True}}, {"embedding": 1}):
        v = np.array(d["embedding"])
        out[d["_id"]] = float(q @ v / (np.linalg.norm(q) * np.linalg.norm(v)))
    return out


def near_duplicates(recent_ids: list[str]) -> set[str]:
    """Quests too similar to the last few the player saw."""
    dupes = set()
    with sentry_sdk.start_span(op="db.vector_search", name="Quest dedupe") as span:
        for qid in recent_ids[:3]:
            q = db.quests.find_one({"_id": qid}, {"embedding": 1})
            if not q or "embedding" not in q:
                continue
            sims = _similar_ids_atlas(q["embedding"]) if db.USING_ATLAS else _similar_ids_local(q["embedding"])
            dupes |= {k for k, s in sims.items() if s >= DUPLICATE_THRESHOLD and k != qid}
        span.set_data("dupes", len(dupes))
    return dupes


def candidates(user_id: str, exclude: list[str] | None = None) -> tuple[list[dict], dict]:
    recent = recent_quest_ids(user_id)
    dupes = near_duplicates(recent)
    blocked = set(recent) | dupes | set(exclude or [])
    pool = list(db.quests.find({"rarity": {"$ne": "boss"}}, PUBLIC_FIELDS))
    fresh = [q for q in pool if q["_id"] not in blocked]
    if len(fresh) < 3:  # played everything recently: relax the dedupe, keep the hard excludes
        fresh = [q for q in pool if q["_id"] not in set(exclude or []) | set(recent[:3])]
    return fresh, {"recent": recent, "near_duplicates": sorted(dupes)}


def pick(pool: list[dict]) -> dict:
    return random.choices(pool, weights=[RARITY_WEIGHT[q["rarity"]] for q in pool], k=1)[0]


def weekly_boss(today: str) -> dict:
    bosses = sorted(db.quests.find({"rarity": "boss"}, PUBLIC_FIELDS), key=lambda q: q["_id"])
    iso_year, iso_week, _ = date.fromisoformat(today).isocalendar()
    return bosses[(iso_year * 53 + iso_week) % len(bosses)] | {"week": f"{iso_year}-W{iso_week:02d}"}
