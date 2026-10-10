"""Demo data for testing and showing the game. Everything is tagged demo=True.

  python -m scripts.demo add NotNirav     # Seeds + demo Field Guide cards for that player, plus demo explorers on the leaderboard
  python -m scripts.demo remove           # removes ALL demo data (run before submitting)
"""
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

from app import db, game

DEMO_SEEDS = 1500
CARDS = [
    ("common-myna", "Common Myna", "bird", "Mynas can mimic car alarms, phone rings and even human words.", "common"),
    ("neem-tree", "Neem tree", "tree", "Neem twigs have been used as toothbrushes for thousands of years.", "common"),
    ("common-crow-butterfly", "Common Crow butterfly", "insect", "Birds avoid it because it stores bitter toxins from its caterpillar food.", "uncommon"),
    ("hibiscus", "Hibiscus", "plant", "A single hibiscus flower usually lasts just one day.", "common"),
    ("indian-grey-hornbill", "Indian Grey Hornbill", "bird", "The female seals herself inside a tree hole with mud while nesting.", "rare"),
    ("cumulus-clouds", "Cumulus clouds", "sky", "An average puffy cumulus cloud weighs about as much as 100 elephants.", "common"),
    ("rose-ringed-parakeet", "Rose-ringed Parakeet", "bird", "Wild flocks now live in dozens of cities far from their native range.", "uncommon"),
    ("banyan-tree", "Banyan tree", "tree", "One banyan in Kolkata covers an area bigger than a football field.", "rare"),
]
EXPLORERS = [("TrailMix", "Pimpri-Chinchwad", 1240), ("MossBoss", "Pune", 980), ("SkyGazer_07", "Pimpri-Chinchwad", 760),
             ("PuddleJumper", "Mumbai", 610), ("Neem_Hunter", "Pune", 420), ("SunsetSaanvi", "Bengaluru", 300)]


def add(handle: str):
    u = db.users.find_one({"handle": handle})
    if not u:
        sys.exit(f"No player called {handle}")
    cards = {k: {"key": k, "name": n, "kind": kind, "fact": f, "rarity": r, "first_seen": date.today().isoformat(),
                 "quest": "Demo card", "area": u.get("area"), "demo": True} for k, n, kind, f, r in CARDS}
    give = max(0, DEMO_SEEDS - u.get("demo_seeds", 0))
    db.users.update_one({"_id": u["_id"]}, {"$set": {"field_guide": {**u.get("field_guide", {}), **cards}, "demo_seeds": DEMO_SEEDS},
                                            "$inc": {"seeds": give}})
    rng = random.Random(7)
    monday = date.today() - timedelta(days=date.today().weekday())
    for name, area, xp in EXPLORERS:
        if db.users.find_one({"handle": name}):
            continue
        uid = f"demo-{uuid.uuid4().hex[:12]}"
        n = max(2, xp // 90)
        db.users.insert_one({"_id": uid, "handle": name, "handle_lower": name.lower(), "xp": xp, "seeds": xp // 8, "streak": rng.randint(1, 6),
                             "best_streak": rng.randint(3, 9), "completed": n, "area": area, "badges": ["first-steps"], "camp": {},
                             "field_guide": dict(list(cards.items())[: rng.randint(1, 6)]), "demo": True, "created_at": datetime.now(timezone.utc)})
        for i in range(n):  # this week's completions so they show on the weekly board too
            db.attempts.insert_one({"_id": f"demo-{uuid.uuid4().hex}", "user_id": uid, "outcome": "pass", "xp_awarded": xp // n,
                                    "local_date": (monday + timedelta(days=min(i % 7, date.today().weekday()))).isoformat(),
                                    "demo": True, "created_at": datetime.now(timezone.utc)})
    print(f"{handle}: +{give} Seeds, {len(cards)} demo cards; {len(EXPLORERS)} demo explorers on the leaderboard")


def remove():
    a = db.attempts.delete_many({"demo": True}).deleted_count
    u = db.users.delete_many({"demo": True}).deleted_count
    for p in db.users.find({"demo_seeds": {"$gt": 0}}):
        guide = {k: v for k, v in p.get("field_guide", {}).items() if not v.get("demo")}
        db.users.update_one({"_id": p["_id"]}, {"$set": {"field_guide": guide, "seeds": max(0, p.get("seeds", 0) - p["demo_seeds"])},
                                                "$unset": {"demo_seeds": ""}})
    print(f"removed {u} demo explorers, {a} demo completions, demo Seeds and cards")


if __name__ == "__main__":
    {"add": lambda: add(sys.argv[2]), "remove": remove}[sys.argv[1]]()
