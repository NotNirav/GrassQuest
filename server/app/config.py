import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MONGODB_URI = os.getenv("MONGODB_URI", "")  # empty -> in-memory mongomock (dev only)
MONGODB_DB = os.getenv("MONGODB_DB", "sidequests")
TABPFN_TOKEN = os.getenv("TABPFN_TOKEN", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_flash_v2_5")
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

DATA_DIR = Path(__file__).resolve().parent / "data"

# TabPFN learns from everyone's history (incl. "this player has 0 attempts"), so it can score new players too
TABPFN_MIN_USER_ATTEMPTS = int(os.getenv("TABPFN_MIN_USER_ATTEMPTS", "0"))

# Free-tier guard. Real limits (Oct 2026): 5M tokens/day, 20M/month. Defaults stop at 75%; local .env uses 50%.
TABPFN_DAILY_CAP = int(os.getenv("TABPFN_DAILY_CAP", "3750000"))
TABPFN_MONTHLY_CAP = int(os.getenv("TABPFN_MONTHLY_CAP", "15000000"))
TABPFN_MAX_CALLS_PER_MINUTE = int(os.getenv("TABPFN_MAX_CALLS_PER_MINUTE", "30"))
TABPFN_MAX_CALLS_PER_USER_DAY = int(os.getenv("TABPFN_MAX_CALLS_PER_USER_DAY", "40"))

# ElevenLabs free tier: 10k credits/month (~0.5 credit/char on flash). Default cap 14k chars ≈ 7k credits (70%).
ELEVENLABS_MONTHLY_CHAR_CAP = int(os.getenv("ELEVENLABS_MONTHLY_CHAR_CAP", "0"))  # 0 = no new runtime lines; only pre-made clips play
ELEVENLABS_MAX_LINES_PER_USER_DAY = int(os.getenv("ELEVENLABS_MAX_LINES_PER_USER_DAY", "15"))
