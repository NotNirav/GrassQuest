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
context_cache = db.context_cache
templates = db.templates


def _load(name):
    return json.loads((config.DATA_DIR / name).read_text(encoding="utf-8"))


def ensure_seeded():
    """Load the v2 quest library if the database doesn't have it yet (build it with scripts/build_quests.py)."""
    if quests.find_one({"template_id": {"$exists": True}}):
        return
    quests.delete_many({})
    for q in _load("quests_v2.json"):
        quests.replace_one({"_id": q["_id"]}, q, upsert=True)
    for t in _load("templates_v2.json"):
        templates.replace_one({"_id": t["_id"]}, t, upsert=True)
    attempts.create_index([("user_id", 1), ("created_at", -1)])
    users.create_index("handle_lower", unique=True)
