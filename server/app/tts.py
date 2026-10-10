"""ElevenLabs narration, cached in Mongo so each line is generated once.

Free tier: 10,000 credits/month; eleven_flash_v2_5 costs ~0.5 credit per character.
Guard: stop at ELEVENLABS_MONTHLY_CHAR_CAP characters (default 14k chars ≈ 7k credits = 70%), checked against
our own ledger and, when the key is allowed to read it, ElevenLabs' own usage counter. Cache hits are free.
"""
import hashlib
import logging
import time
from datetime import datetime, timezone

import httpx
import sentry_sdk
from bson.binary import Binary

from . import config, db

log = logging.getLogger(__name__)

MAX_CHARS = 300
CREDITS_PER_CHAR = 0.5  # flash/turbo models
_sub = {"used": None, "limit": None, "checked_at": 0.0}


def enabled() -> bool:
    return bool(config.ELEVENLABS_API_KEY)


def _month():
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _day():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _remote_credits_used() -> int | None:
    """ElevenLabs' own counter. Restricted keys may not be allowed to read it; then we rely on our ledger."""
    if time.time() - _sub["checked_at"] < 600:
        return _sub["used"]
    _sub["checked_at"] = time.time()
    try:
        r = httpx.get("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": config.ELEVENLABS_API_KEY}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            _sub.update(used=int(data.get("character_count", 0)), limit=int(data.get("character_limit", 0)))
    except Exception:
        log.info("Couldn't read ElevenLabs usage; using our own ledger")
    return _sub["used"]


def budget() -> dict:
    ledger = db.tts_usage.find_one({"_id": f"month:{_month()}"}) or {}
    chars = ledger.get("chars", 0)
    remote = _remote_credits_used()
    credits = max(chars * CREDITS_PER_CHAR, remote or 0)
    return {"chars_this_month": chars, "credits_used_est": int(credits), "remote_credits_used": remote,
            "credit_cap": int(config.ELEVENLABS_MONTHLY_CHAR_CAP * CREDITS_PER_CHAR)}


def _allowed(text: str, user_id: str) -> bool:
    b = budget()
    if b["credits_used_est"] + len(text) * CREDITS_PER_CHAR > b["credit_cap"]:
        return False
    per_user = db.tts_usage.find_one({"_id": f"user:{user_id}:{_day()}"}) or {}
    return per_user.get("lines", 0) < config.ELEVENLABS_MAX_LINES_PER_USER_DAY


def speak(text: str, user_id: str) -> bytes | None:
    text = text.strip()[:MAX_CHARS]
    key = hashlib.sha1(f"{config.ELEVENLABS_VOICE_ID}|{config.ELEVENLABS_MODEL}|{text}".encode()).hexdigest()
    hit = db.tts_cache.find_one({"_id": key})
    if hit:
        return bytes(hit["audio"])
    if not enabled() or not db.users.find_one({"_id": user_id}, {"_id": 1}) or not _allowed(text, user_id):
        return None  # client falls back to the browser's own voice
    with sentry_sdk.start_span(op="ai.tts", name="ElevenLabs TTS") as span:
        span.set_data("chars", len(text))
        r = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}",
            params={"output_format": "mp3_44100_64"},
            headers={"xi-api-key": config.ELEVENLABS_API_KEY},
            json={"text": text, "model_id": config.ELEVENLABS_MODEL},
            timeout=30,
        )
        r.raise_for_status()
    db.tts_usage.update_one({"_id": f"month:{_month()}"}, {"$inc": {"chars": len(text), "lines": 1}}, upsert=True)
    db.tts_usage.update_one({"_id": f"user:{user_id}:{_day()}"}, {"$inc": {"lines": 1}}, upsert=True)
    db.tts_cache.replace_one({"_id": key}, {"_id": key, "text": text, "audio": Binary(r.content)}, upsert=True)
    return r.content
