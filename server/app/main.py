import logging
import uuid
from datetime import date, datetime, timedelta, timezone

import sentry_sdk
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, context, db, difficulty, game, quests, tts

if config.SENTRY_DSN:
    sentry_sdk.init(dsn=config.SENTRY_DSN, traces_sample_rate=1.0, send_default_pii=False)

log = logging.getLogger(__name__)
app = FastAPI(title="GrassQuest API")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])
db.ensure_seeded()


@app.on_event("startup")
def warm_tabpfn():
    # fitting is free but slow (~10 s); do it in the background so the first player doesn't wait for it
    import threading

    threading.Thread(target=difficulty.warm, daemon=True).start()


def now():
    return datetime.now(timezone.utc)


def get_user(user_id: str) -> dict:
    user = db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(404, "Unknown player")
    return user


def settle(user: dict, today: str) -> dict:
    """Apply streak freezes for missed days before showing or changing anything."""
    changes = game.settle_streak(user, today)
    if changes:
        db.users.update_one({"_id": user["_id"]}, {"$set": changes})
        user = {**user, **changes}
    return user


def public_user(user: dict, today: str) -> dict:
    guide = user.get("field_guide", {})
    return {
        "id": user["_id"], "handle": user["handle"], **game.level_info(user.get("xp", 0)),
        "seeds": user.get("seeds", 0), "streak": game.live_streak(user, today), "best_streak": user.get("best_streak", 0),
        "freezes": user.get("freezes", 0), "max_freezes": game.MAX_FREEZES, "freeze_price": game.FREEZE_PRICE,
        "completed": user.get("completed", 0), "counts": user.get("counts", {}), "area": user.get("area"),
        "badges": [game.badge_view(b) for b in user.get("badges", []) if b in game.BADGES],
        "camp": game.camp_view(user.get("camp", {})),
        "field_guide": sorted(guide.values(), key=lambda c: c["first_seen"], reverse=True),
    }


# ---------- players ----------
class NewUser(BaseModel):
    handle: str = Field(min_length=2, max_length=24, pattern=r"^[A-Za-z0-9_\- ]+$")


@app.post("/api/users")
def create_user(body: NewUser):
    handle = body.handle.strip()
    if db.users.find_one({"handle_lower": handle.lower()}):
        raise HTTPException(409, "That name is taken. Pick another one.")
    user = {"_id": uuid.uuid4().hex, "handle": handle, "handle_lower": handle.lower(), "xp": 0, "seeds": 0, "streak": 0,
            "best_streak": 0, "freezes": 0, "completed": 0, "counts": {}, "badges": [], "camp": {}, "field_guide": {},
            "created_at": now()}
    db.users.insert_one(user)
    return public_user(user, date.today().isoformat())


@app.get("/api/users/{user_id}")
def read_user(user_id: str, today: str):
    return public_user(settle(get_user(user_id), today), today)


# ---------- world ----------
class Where(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


def ctx_view(ctx: dict) -> dict:
    return {k: ctx[k] for k in ("cell", "area", "weather", "sun", "places", "features", "places_loading")}  # no exact coordinates


@app.post("/api/context")
def world(body: Where):
    try:
        return ctx_view(context.build(body.lat, body.lon))
    except Exception as e:
        log.exception("context failed")
        raise HTTPException(502, f"Couldn't read the weather for this spot ({type(e).__name__}). Try again in a minute.")


@app.get("/api/geocode")
def geocode(q: str, lat: float | None = None, lon: float | None = None):
    if len(q.strip()) < 2:
        return []
    try:
        return context.search_place(q.strip(), (lat, lon) if lat is not None and lon is not None else None)
    except Exception:
        log.exception("place search failed")
        raise HTTPException(502, "Place search is busy. Try again in a moment.")


# ---------- quests ----------
class Today(Where):
    user_id: str
    exclude: list[str] = []


def fill_place(q: dict, ctx: dict) -> dict:
    place = context.place_for(ctx, q["needs"])
    title = q["title"].replace("{place}", place["name"] if place else "somewhere nearby")
    return {**q, "title": title, "place": place}


@app.post("/api/quests/today")
def today_quests(body: Today):
    user = get_user(body.user_id)
    ctx = context.build(body.lat, body.lon)
    today = ctx["sun"]["local_date"]
    user = settle(user, today)
    streak = game.live_streak(user, today)

    rain_check = ctx["weather"]["band"] == "severe"
    if rain_check and user.get("rain_check_date") != today and user.get("freezes", 0) < game.MAX_FREEZES:
        db.users.update_one({"_id": user["_id"]}, {"$inc": {"freezes": 1}, "$set": {"rain_check_date": today}})
    if ctx["area"].get("city"):
        db.users.update_one({"_id": user["_id"]}, {"$set": {"area": ctx["area"]["city"]}})

    everything = quests.eligible(ctx)
    scores = difficulty.score(user["_id"], everything, ctx, streak)  # one cached TabPFN call covers every eligible quest
    pool, meta = quests.candidates(user["_id"], everything, body.exclude)
    picks = quests.three_choices([(q, scores[q["_id"]]) for q in pool])

    choices = []
    for slot, q, s in picks:
        q = fill_place(q, ctx)
        rewards = game.quest_rewards(q, s["p"], streak)
        offer = {
            "_id": uuid.uuid4().hex, "user_id": user["_id"], "quest_id": q["_id"], "template_id": q["template_id"],
            "cat": q["cat"], "rarity": q["rarity"], "slot": slot, "outcome": "offered", "accepted": False, "fails": 0,
            "p_complete": s["p"], "p_source": s["source"], "minutes_pred": s["minutes"], "features": s["features"],
            "rewards": rewards, "weather": {k: ctx["weather"][k] for k in ("band", "temp", "label")},
            "local_date": today, "cell": ctx["cell"], "synthetic": False, "created_at": now(),
        }
        db.attempts.insert_one(offer)
        choices.append({"offer_id": offer["_id"], "slot": slot, "quest": q, "p": s["p"], "minutes": s["minutes"],
                        "source": s["source"], **rewards})
    return {"context": ctx_view(ctx), "choices": choices, "rain_check": rain_check, "meta": meta,
            "player": public_user(get_user(user["_id"]), today)}


def get_offer(offer_id: str) -> dict:
    offer = db.attempts.find_one({"_id": offer_id})
    if not offer:
        raise HTTPException(404, "Unknown quest")
    return offer


@app.post("/api/offers/{offer_id}/accept")
def accept(offer_id: str):
    offer = get_offer(offer_id)
    db.attempts.update_one({"_id": offer_id}, {"$set": {"accepted": True, "accepted_at": now()}})
    return {"ok": True, "offer_id": offer["_id"]}


class Identified(BaseModel):
    kind: str = Field(default="none", max_length=20)
    name: str = Field(default="", max_length=60)
    fact: str = Field(default="", max_length=200)
    rarity: str = Field(default="common", max_length=12)


class Verdict(BaseModel):
    verdict: str = Field(pattern="^(pass|close|no)$")
    confidence: float = Field(ge=0, le=1)
    seen: str = Field(default="", max_length=200)
    reaction: str = Field(default="", max_length=300)
    identified: Identified | None = None
    model: str = Field(default="", max_length=60)


@app.post("/api/offers/{offer_id}/verdict")
def submit_verdict(offer_id: str, body: Verdict):
    """The photo is judged by the player's local Gemma. Only this verdict reaches the server, never the photo."""
    offer = get_offer(offer_id)
    if offer["outcome"] != "offered":
        raise HTTPException(409, "This quest is already finished")
    user = get_user(offer["user_id"])
    record = body.model_dump()
    today = offer["local_date"]

    if body.verdict == "no":
        db.attempts.update_one({"_id": offer_id}, {"$inc": {"fails": 1}, "$push": {"verdicts": record}})
        return {"verdict": "no", "fails": offer["fails"] + 1}

    q = db.quests.find_one({"_id": offer["quest_id"]})
    share = 1.0 if body.verdict == "pass" else game.CLOSE_ENOUGH
    xp, seeds = round(offer["rewards"]["xp"] * share), round(offer["rewards"]["seeds"] * share)

    # Field Guide: Gemma named what it saw
    new_card, card_seeds = None, 0
    ident = body.identified
    guide = dict(user.get("field_guide", {}))
    if ident and ident.kind in game.KINDS and ident.name.strip():
        key = game.card_key(ident.name)
        if key and key not in guide:
            rarity = ident.rarity if ident.rarity in game.FIELD_CARD_SEEDS else "common"
            new_card = {"key": key, "name": ident.name.strip()[:60], "kind": ident.kind, "fact": ident.fact.strip()[:200],
                        "rarity": rarity, "first_seen": today, "quest": q["title"].replace("{place}", "").strip(),
                        "area": user.get("area")}
            guide[key] = new_card
            card_seeds = game.FIELD_CARD_SEEDS[rarity]

    streak = game.next_streak(game.live_streak(user, today), user.get("last_active_date"), today)
    counts = {**user.get("counts", {})}
    counts[q["cat"]] = counts.get(q["cat"], 0) + 1
    updated = {**user, "streak": streak, "counts": counts, "field_guide": guide}
    new_badges = game.earned_badges(updated, q, offer, offer.get("weather"))
    before = game.level_for(user.get("xp", 0))
    duration = round((now() - offer["accepted_at"].replace(tzinfo=timezone.utc)).total_seconds() / 60, 1) if offer.get("accepted_at") else None

    db.users.update_one({"_id": user["_id"]}, {
        "$inc": {"xp": xp, "seeds": seeds + card_seeds, "completed": 1},
        "$set": {"streak": streak, "best_streak": max(streak, user.get("best_streak", 0)), "counts": counts,
                 "last_active_date": today, "field_guide": guide},
        "$push": {"badges": {"$each": new_badges}},
    })
    db.attempts.update_one({"_id": offer_id}, {"$set": {"outcome": "pass", "share": share, "xp_awarded": xp, "seeds_awarded": seeds,
                                                        "completed_at": now(), "duration_min": duration},
                                               "$push": {"verdicts": record}})
    fresh = public_user(get_user(user["_id"]), today)
    return {"verdict": body.verdict, "xp": xp, "seeds": seeds, "card_seeds": card_seeds, "new_card": new_card,
            "level_up": fresh["level"] > before, "new_badges": [game.badge_view(b) for b in new_badges], "player": fresh}


@app.post("/api/offers/{offer_id}/giveup")
def give_up(offer_id: str):
    offer = get_offer(offer_id)
    if offer["outcome"] == "offered" and offer.get("accepted"):
        db.attempts.update_one({"_id": offer_id}, {"$set": {"outcome": "fail" if offer["fails"] else "skip"}})
    return {"ok": True}


# ---------- economy ----------
class Buy(BaseModel):
    user_id: str
    today: str


class BuyCamp(Buy):
    slot: str


@app.post("/api/camp/buy")
def buy_camp(body: BuyCamp):
    user = get_user(body.user_id)
    if body.slot not in game.CAMP:
        raise HTTPException(400, "Unknown camp slot")
    camp = dict(user.get("camp", {}))
    tier = camp.get(body.slot, 0)
    tiers = game.CAMP[body.slot]["tiers"]
    if tier + 1 >= len(tiers):
        raise HTTPException(409, "Already fully upgraded")
    price = tiers[tier + 1][1]
    # atomic: only spend if the player still has the seeds and the tier hasn't changed
    res = db.users.update_one({"_id": user["_id"], "seeds": {"$gte": price}, f"camp.{body.slot}": camp.get(body.slot) if body.slot in camp else {"$exists": False}},
                              {"$inc": {"seeds": -price}, "$set": {f"camp.{body.slot}": tier + 1}})
    if not res.modified_count:
        raise HTTPException(409, f"You need {price} Seeds for that")
    user = get_user(user["_id"])
    if all(user.get("camp", {}).get(s, 0) >= 1 for s in game.CAMP) and "homesteader" not in user.get("badges", []):
        db.users.update_one({"_id": user["_id"]}, {"$push": {"badges": "homesteader"}})
    return public_user(get_user(user["_id"]), body.today)


@app.post("/api/freeze/buy")
def buy_freeze(body: Buy):
    res = db.users.update_one({"_id": body.user_id, "seeds": {"$gte": game.FREEZE_PRICE}, "freezes": {"$lt": game.MAX_FREEZES}},
                              {"$inc": {"seeds": -game.FREEZE_PRICE, "freezes": 1}})
    if not res.modified_count:
        raise HTTPException(409, f"Freezes cost {game.FREEZE_PRICE} Seeds and you can hold {game.MAX_FREEZES}")
    return public_user(get_user(body.user_id), body.today)


@app.get("/api/badges")
def badges():
    return [game.badge_view(k) for k in game.BADGES]


# ---------- leaderboard ----------
@app.get("/api/leaderboard")
def leaderboard(scope: str = "week", today: str | None = None, area: str | None = None):
    if scope in ("all", "area"):
        q = {"area": area} if scope == "area" and area else {}
        return [{"id": u["_id"], "handle": u["handle"], "xp": u.get("xp", 0), "quests": u.get("completed", 0), "area": u.get("area"),
                 "level": game.level_for(u.get("xp", 0)), "cards": len(u.get("field_guide", {}))}
                for u in db.users.find(q).sort([("xp", -1), ("created_at", 1)]).limit(50)]
    match = {"outcome": "pass", "synthetic": {"$ne": True}}
    if scope == "week":
        d = date.fromisoformat(today) if today else date.today()
        match["local_date"] = {"$gte": (d - timedelta(days=d.weekday())).isoformat()}
    rows = list(db.attempts.aggregate([
        {"$match": match},
        {"$group": {"_id": "$user_id", "xp": {"$sum": "$xp_awarded"}, "quests": {"$sum": 1}}},
        {"$sort": {"xp": -1}}, {"$limit": 200},
    ]))
    users = {u["_id"]: u for u in db.users.find({"_id": {"$in": [r["_id"] for r in rows]}})}
    out = []
    for r in rows:
        u = users.get(r["_id"])
        if not u:
            continue
        out.append({"id": r["_id"], "handle": u["handle"], "xp": r["xp"], "quests": r["quests"], "area": u.get("area"),
                    "level": game.level_for(u.get("xp", 0)), "cards": len(u.get("field_guide", {}))})
    return out[:50]


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
        log.warning("ElevenLabs failed, browser voice will be used: %s %s", e, detail)
        audio = None
    if not audio:
        return Response(status_code=204)
    return Response(audio, media_type="audio/mpeg", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/health")
def health():
    return {"ok": True, "db": "atlas" if db.USING_ATLAS else "in-memory (dev)", "quests": db.quests.count_documents({}),
            "templates": db.templates.count_documents({}), "tts": {"enabled": tts.enabled(), **tts.budget()},
            "difficulty": difficulty.status(), "sentry": bool(config.SENTRY_DSN)}
