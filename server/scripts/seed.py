"""One-off setup.

  python -m scripts.seed embed       # embed quests with local Ollama bge-m3 -> app/data/quests_embedded.json
  python -m scripts.seed load        # upsert quests (+ embeddings) into MongoDB and create the Atlas vector index
  python -m scripts.seed synthetic   # add SYNTHETIC attempt rows (synthetic=True) so TabPFN has something to learn from on day one

Run from the server/ folder.
"""
import json
import random
import sys
import urllib.request
import uuid
from datetime import date, datetime, timedelta, timezone

from app import config, db, difficulty

OLLAMA = "http://localhost:11434"
EMBED_MODEL = "bge-m3"


def embed(text: str) -> list[float]:
    req = urllib.request.Request(f"{OLLAMA}/api/embed", json.dumps({"model": EMBED_MODEL, "input": text}).encode(),
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())["embeddings"][0]


def cmd_embed():
    pool = db._load("quests.json") + db._load("boss_quests.json")
    for q in pool:
        q["embedding"] = embed(f"{q['title']}. {q['proof']}")
        print("embedded", q["id"])
    (config.DATA_DIR / "quests_embedded.json").write_text(json.dumps(pool), encoding="utf-8")
    print(f"wrote {len(pool)} quests, dim={len(pool[0]['embedding'])}")


def cmd_load():
    pool = db._load("quests_embedded.json")
    for q in pool:
        db.quests.replace_one({"_id": q["id"]}, {**q, "_id": q["id"]}, upsert=True)
    print(f"upserted {len(pool)} quests into {'Atlas' if db.USING_ATLAS else 'in-memory db'}")
    if db.USING_ATLAS:
        from pymongo.operations import SearchIndexModel

        existing = [i["name"] for i in db.quests.list_search_indexes()]
        if "quest_embedding_index" not in existing:
            db.quests.create_search_index(SearchIndexModel(
                name="quest_embedding_index", type="vectorSearch",
                definition={"fields": [{"type": "vector", "path": "embedding", "numDimensions": len(pool[0]["embedding"]),
                                        "similarity": "cosine"}]},
            ))
            print("created vector search index (takes ~1 min to become queryable)")


def cmd_synthetic(n: int = 300):
    """Clearly-labelled fake history. The write-up must say these are synthetic."""
    random.seed(42)
    pool = db._load("quests.json") + db._load("boss_quests.json")
    rows = []
    for i in range(n):
        q = random.choice(pool)
        hour, dow = random.randint(5, 23), random.randint(0, 6)
        attempts_so_far = random.randint(0, 40)
        skill = random.uniform(0.3, 0.9)
        streak = random.randint(0, 10)
        stats = {"attempts": attempts_so_far, "pass_rate": skill}
        quest = {**q, "_id": q["id"]}
        p = difficulty.heuristic(quest, hour, stats)
        p = min(0.97, p + 0.02 * min(streak, 5) + (0.08 if dow >= 5 else 0))  # weekends + streaks help
        outcome = "pass" if random.random() < p else random.choice(["fail", "skip"])
        feats = difficulty.feature_row(quest, hour, dow, streak, stats, 0.5)
        rows.append({
            "_id": f"synthetic-{uuid.uuid4().hex}", "user_id": f"synthetic-user-{i % 12}", "quest_id": q["id"],
            "category": q["category"], "rarity": q["rarity"], "outcome": outcome, "fails": 0, "p_complete": p,
            "features": dict(zip(difficulty.FEATURES, feats)), "synthetic": True,
            "local_date": (date.today() - timedelta(days=random.randint(1, 30))).isoformat(),
            "created_at": datetime.now(timezone.utc) - timedelta(days=30),
        })
    db.attempts.delete_many({"synthetic": True})
    db.attempts.insert_many(rows)
    print(f"inserted {len(rows)} SYNTHETIC rows ({sum(r['outcome'] == 'pass' for r in rows)} passes)")


if __name__ == "__main__":
    {"embed": cmd_embed, "load": cmd_load, "synthetic": cmd_synthetic}[sys.argv[1]]()
