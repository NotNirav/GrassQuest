"""ElevenLabs narration, cached in Mongo so each line is generated once."""
import hashlib

import httpx
import sentry_sdk
from bson.binary import Binary

from . import config, db

MAX_CHARS = 300


def enabled() -> bool:
    return bool(config.ELEVENLABS_API_KEY)


def speak(text: str) -> bytes | None:
    text = text.strip()[:MAX_CHARS]
    key = hashlib.sha1(f"{config.ELEVENLABS_VOICE_ID}|{config.ELEVENLABS_MODEL}|{text}".encode()).hexdigest()
    hit = db.tts_cache.find_one({"_id": key})
    if hit:
        return bytes(hit["audio"])
    if not enabled():
        return None
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
    db.tts_cache.replace_one({"_id": key}, {"_id": key, "text": text, "audio": Binary(r.content)}, upsert=True)
    return r.content
