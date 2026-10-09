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

# a user needs this many attempts before TabPFN replaces the heuristic
TABPFN_MIN_USER_ATTEMPTS = int(os.getenv("TABPFN_MIN_USER_ATTEMPTS", "5"))
