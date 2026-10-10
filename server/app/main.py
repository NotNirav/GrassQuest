import logging
import uuid
from datetime import date, datetime, timedelta, timezone

import sentry_sdk
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, db, difficulty, game, quests, tts

if config.SENTRY_DSN:
    sentry_sdk.init(dsn=config.SENTRY_DSN, traces_sample_rate=1.0, send_default_pii=False)

app = FastAPI(title="GrassQuest API")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
db.ensure_seeded()
if not db.USING_ATLAS:
    # dev mode keeps everything in memory, so re-create the labelled synthetic history on each start
    from scripts.seed import cmd_synthetic

    cmd_synthetic()


def now():
    return datetime.now(timezone.utc)


def get_user(user_id: str) -> dict:
    user = db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "Unknown player")
    return user


def public_user(user: dict, today: str | None = None) -> dict:
    today = today or date.today().isoformat()
    return {
        "id": user["_id"],
        "handle": user["handle"],
        **game.level_info(user.get("xp", 0)),
        "streak": game.live_streak(user, today),
        "best_streak": user.get("best_streak", 0),
        "completed": user.get("completed", 0),
        "counts": user.get("counts", {}),
        "badges": [game.badge_view(b) for b in user.get("badges", [])],
    }


# ---------- players ----------
class NewUser(BaseModel):
    handle: str = Field(min_length=2, max_length=24, pattern=r"^[A-Za-z0-9_\- ]+$")


@app.post("/api/users")
def create_user(body: NewUser):
    handle = body.handle.strip()
    existing = db.users.find_one({"handle_lower": handle.lower()})
    if existing:
        raise HTTPException(409, "That name is taken. Pick another one.")
    user = {"_id": uuid.uuid4().hex, "handle": handle, "handle_lower": handle.lower(), "xp": 0, "streak": 0,
            "best_streak": 0, "completed": 0, "counts": {}, "badges": [], "created_at": now()}
    db.users.insert_one(user)
    return public_user(user)


@app.get("/api/users/{user_id}")
def read_user(user_id: str, today: str | None = None):
    return public_user(get_user(user_id), today)


# ---------- quests ----------
class Clock(BaseModel):
    """The player's local clock, so streaks and 'Early Bird' follow their timezone."""
    today: str  # YYYY-MM-DD
    hour: int = Field(ge=0, le=23)
    dow: int = Field(ge=0, le=6)  # 0 = Monday


class NextQuest(Clock):
    user_id: str
    exclude: list[str] = []
    boss: bool = False


def make_offer(user: dict, quest: dict, clock: Clock, p: float, feats: list, source: str, extra: dict | None = None) -> dict:
    streak = game.live_streak(user, clock.today)
    xp = game.quest_xp(quest["rarity"], p, streak)
    offer = {
        "_id": uuid.uuid4().hex, "user_id": user["_id"], "quest_id": quest["_id"], "category": quest["category"],
        "rarity": quest["rarity"], "outcome": "offered", "fails": 0, "p_complete": p, "p_source": source,
        "xp_offered": xp, "features": dict(zip(difficulty.FEATURES, feats)), "local_date": clock.today,
        "synthetic": False, "created_at": now(),
    }
    db.attempts.insert_one(offer)
    return {
        "offer_id": offer["_id"], "quest": quest, "p_complete": p, "p_source": source,
        "multiplier": game.xp_multiplier(p), "streak_bonus": game.streak_bonus(streak), "xp": xp, **(extra or {}),
    }


@app.post("/api/quests/next")
def next_quest(body: NextQuest):
    user = get_user(body.user_id)
    streak = game.live_streak(user, body.today)
    if body.boss:
        quest = quests.weekly_boss(body.today)
        done = db.attempts.find_one({"user_id": user["_id"], "quest_id": quest["_id"], "outcome": "pass",
                                     "local_date": {"$gte": (date.fromisoformat(body.today) - timedelta(days=body.dow)).isoformat()}})
        if done:
            return {"boss_done": True, "quest": quest}
        pool, why = [quest], {}
    else:
        pool, why = quests.candidates(user["_id"], body.exclude)
    probs, feats, source = difficulty.predict(user["_id"], pool, body.hour, body.dow, streak)
    if body.boss:
        i = 0
    else:
        chosen = quests.pick(pool)
        i = next(k for k, q in enumerate(pool) if q["_id"] == chosen["_id"])
    return make_offer(user, pool[i], body, probs[i], feats[i], source, {"dedupe": why})


class Verdict(Clock):
    passed: bool
    confidence: float = Field(ge=0, le=1)
    seen: str = Field(default="", max_length=200)
    reaction: str = Field(default="", max_length=300)
    model: str = Field(default="", max_length=60)


@app.post("/api/offers/{offer_id}/verdict")
def submit_verdict(offer_id: str, body: Verdict):
    """The photo is judged by the player's local Gemma. Only the verdict comes here, never the photo."""
    offer = db.attempts.find_one({"_id": offer_id})
    if not offer:
        raise HTTPException(404, "Unknown quest offer")
    if offer["outcome"] != "offered":
        raise HTTPException(409, "This quest is already finished")
    user = get_user(offer["user_id"])
    verdict = {"confidence": body.confidence, "seen": body.seen, "reaction": body.reaction, "model": body.model}

    if not body.passed:
        db.attempts.update_one({"_id": offer_id}, {"$inc": {"fails": 1}, "$push": {"verdicts": verdict}})
        return {"passed": False, "fails": offer["fails"] + 1}

    quest = db.quests.find_one({"_id": offer["quest_id"]}, quests.PUBLIC_FIELDS)
    streak = game.next_streak(game.live_streak(user, body.today), user.get("last_active_date"), body.today)
    xp = offer["xp_offered"]  # pay exactly what the quest card promised
    counts = {**user.get("counts", {})}
    counts[quest["category"]] = counts.get(quest["category"], 0) + 1
    updated = {**user, "streak": streak, "counts": counts}
    new_badges = game.earned_badges(updated, quest, body.hour, offer["p_complete"])
    before = game.level_for(user.get("xp", 0))

    db.users.update_one({"_id": user["_id"]}, {
        "$inc": {"xp": xp, "completed": 1},
        "$set": {"streak": streak, "best_streak": max(streak, user.get("best_streak", 0)), "counts": counts,
                 "last_active_date": body.today},
        "$push": {"badges": {"$each": new_badges}},
    })
    db.attempts.update_one({"_id": offer_id}, {"$set": {"outcome": "pass", "xp_awarded": xp, "completed_at": now()},
                                               "$push": {"verdicts": verdict}})
    fresh = public_user(get_user(user["_id"]), body.today)
    return {"passed": True, "xp": xp, "level_up": fresh["level"] > before, "new_badges": [game.badge_view(b) for b in new_badges],
            "player": fresh}


@app.post("/api/offers/{offer_id}/giveup")
def give_up(offer_id: str):
    offer = db.attempts.find_one({"_id": offer_id})
    if not offer:
        raise HTTPException(404, "Unknown quest offer")
    if offer["outcome"] == "offered":
        db.attempts.update_one({"_id": offer_id}, {"$set": {"outcome": "fail" if offer["fails"] else "skip"}})
    return {"ok": True}


@app.get("/api/badges")
def badges():
    return [game.badge_view(k) for k in game.BADGES]


# ---------- leaderboard ----------
@app.get("/api/leaderboard")
def leaderboard(scope: str = "all", today: str | None = None):
    if scope == "week":
        d = date.fromisoformat(today) if today else date.today()
        monday = (d - timedelta(days=d.weekday())).isoformat()
        rows = list(db.attempts.aggregate([
            {"$match": {"outcome": "pass", "synthetic": {"$ne": True}, "local_date": {"$gte": monday}}},
            {"$group": {"_id": "$user_id", "xp": {"$sum": "$xp_awarded"}, "quests": {"$sum": 1}}},
            {"$sort": {"xp": -1}}, {"$limit": 50},
        ]))
        names = {u["_id"]: u for u in db.users.find({"_id": {"$in": [r["_id"] for r in rows]}})}
        return [{"id": r["_id"], "handle": names[r["_id"]]["handle"], "xp": r["xp"], "quests": r["quests"],
                 "level": game.level_for(names[r["_id"]].get("xp", 0))} for r in rows if r["_id"] in names]
    users = db.users.find({}, {"handle": 1, "xp": 1, "completed": 1}).sort("xp", -1).limit(50)
    return [{"id": u["_id"], "handle": u["handle"], "xp": u.get("xp", 0), "quests": u.get("completed", 0),
             "level": game.level_for(u.get("xp", 0))} for u in users]


# ---------- voice ----------
class Speak(BaseModel):
    text: str = Field(min_length=1, max_length=tts.MAX_CHARS)
    user_id: str


@app.post("/api/tts")
def speak(body: Speak):
    try:
        audio = tts.speak(body.text, body.user_id)
    except Exception as e:
        detail = getattr(getattr(e, "response", None), "text", "")[:300]
        logging.getLogger(__name__).warning("ElevenLabs failed, browser voice will be used: %s %s", e, detail)
        audio = None
    if not audio:
        return Response(status_code=204)  # client falls back to the browser's own voice
    return Response(audio, media_type="audio/mpeg", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/health")
def health():
    return {"ok": True, "db": "atlas" if db.USING_ATLAS else "in-memory (dev)", "quests": db.quests.count_documents({}),
            "tts": {"enabled": tts.enabled(), **tts.budget()}, "difficulty": difficulty.status(), "sentry": bool(config.SENTRY_DSN)}
