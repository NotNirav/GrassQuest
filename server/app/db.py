import json

from . import config

if config.MONGODB_URI:
    from pymongo import MongoClient

    client = MongoClient(config.MONGODB_URI)
    USING_ATLAS = True
else:
    import mongomock

    client = mongomock.MongoClient()
    USING_ATLAS = False

db = client[config.MONGODB_DB]
users = db.users
attempts = db.attempts
quests = db.quests
tts_cache = db.tts_cache
tabpfn_usage = db.tabpfn_usage
tts_usage = db.tts_usage


def _load(name):
    return json.loads((config.DATA_DIR / name).read_text(encoding="utf-8"))


def ensure_seeded():
    """Make sure the quest pool exists. Embeddings come from scripts/seed.py."""
    if quests.count_documents({}) > 0:
        return
    embedded = config.DATA_DIR / "quests_embedded.json"
    pool = _load("quests_embedded.json") if embedded.exists() else _load("quests.json") + _load("boss_quests.json")
    for q in pool:
        quests.replace_one({"_id": q["id"]}, {**q, "_id": q["id"]}, upsert=True)
    attempts.create_index([("user_id", 1), ("created_at", -1)])
    users.create_index("handle_lower", unique=True)
