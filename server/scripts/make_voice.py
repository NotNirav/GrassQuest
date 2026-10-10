"""Generate the Ranger's voice lines ONCE with ElevenLabs and save them as static files.

  python -m scripts.make_voice          # dry run: shows lines and character count
  python -m scripts.make_voice --go     # generates only files that don't exist yet (never re-spends credits)

Files land in web/public/voice/<id>.mp3 and are served with the website; no ElevenLabs call happens while people play.
"""
import sys
from pathlib import Path

import httpx

from app import config

OUT = Path(__file__).resolve().parents[2] / "web" / "public" / "voice"

LINES = {
    "welcome": "Welcome, Adventurer. I'm the Ranger. I'll find the quests. You bring the legs.",
    "go-clear": "Clear skies, Adventurer. The world is wide open today. Pocket the phone and go find it.",
    "go-cloudy": "Grey skies make for quiet streets. Perfect for noticing things. Off you go.",
    "go-rain": "A little rain never stopped a real explorer. Hood up, eyes open.",
    "go-hot": "It's a hot one. Stick to the shade, bring water, and keep it short and sweet.",
    "go-golden": "Golden hour, Adventurer. The best light of the day is waiting. Don't waste it.",
    "go-night": "The night shift begins. Look up, listen close, and stay where it's safe.",
    "go-morning": "Early start. The birds are already up. Go and say hello.",
    "pass": "Quest complete. That's how it's done, Adventurer.",
    "close": "Close enough. Half the glory still counts.",
    "no": "Not quite. Take another look around. It's out there.",
    "level-up": "You've levelled up. The outside is starting to recognise you.",
    "new-card": "A new entry for your Field Guide. Your neighbourhood just got a little bigger.",
    "rain-check": "Too wild out there today. Open a window instead. Your streak is safe with me.",
    "streak": "Another day, another step. Your streak lives on.",
    "stretch": "A stretch quest. Bold choice. I like it.",
}


def main():
    todo = {k: v for k, v in LINES.items() if not (OUT / f"{k}.mp3").exists()}
    chars = sum(len(v) for v in todo.values())
    print(f"{len(todo)} of {len(LINES)} lines to generate, {chars} characters (~{chars // 2}-{chars} credits)")
    if "--go" not in sys.argv:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for k, text in todo.items():
        r = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{config.ELEVENLABS_VOICE_ID}",
            params={"output_format": "mp3_44100_64"},
            headers={"xi-api-key": config.ELEVENLABS_API_KEY},
            json={"text": text, "model_id": config.ELEVENLABS_MODEL, "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.35}},
            timeout=60,
        )
        if r.status_code != 200:
            print("stopped:", k, r.status_code, r.text[:200])
            return
        (OUT / f"{k}.mp3").write_bytes(r.content)
        print(f"saved {k}.mp3 ({len(r.content) // 1024} KB)")


if __name__ == "__main__":
    main()
