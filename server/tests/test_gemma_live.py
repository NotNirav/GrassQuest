"""Tests local Gemma 4 integration with Ollama (http://127.0.0.1:11434).
Tests:
1. Model detection
2. Quest briefing personalization (structured output format)
3. Image judging with mock/test image (structured output format)
"""
import base64
import json
import time
import requests

OLLAMA_URL = "http://127.0.0.1:11434"

def test_gemma():
    print("=" * 60)
    print("GEMMA 4 LOCAL AI TEST SUITE (via Ollama)")
    print("=" * 60)

    # 1. Check tags
    r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
    assert r.status_code == 200, f"Ollama not responding: {r.status_code}"
    models = [m["name"] for m in r.json().get("models", [])]
    gemma_models = [m for m in models if "gemma4" in m.lower()]
    print(f"[PASS] Ollama running. Gemma 4 models found: {gemma_models}")
    assert len(gemma_models) > 0, "No Gemma 4 model installed in Ollama"

    model = "gemma4:e2b" if "gemma4:e2b" in gemma_models else gemma_models[0]
    print(f"Testing with model: {model}")

    # 2. Test personalization schema
    BRIEFING_SCHEMA = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "briefing": {"type": "string"},
            "tip": {"type": "string"}
        },
        "required": ["title", "briefing", "tip"],
    }

    facts = {
        "quest": "Find a tree with textured bark",
        "good_proof": "A close up photo of tree bark showing its texture",
        "destination": {"name": "Cubbon Park", "distance_m": 450, "direction": "north"},
        "area": "Bengaluru",
        "weather": {"temp_c": 24, "sky": "partly cloudy", "rain_expected_at": None},
        "time_of_day": "golden",
        "minutes_to_sunset": 45,
    }

    t0 = time.time()
    chat_body = {
        "model": model,
        "format": BRIEFING_SCHEMA,
        "options": {"temperature": 0.8, "num_predict": 500},
        "think": False,
        "stream": False,
        "keep_alive": "30m",
        "messages": [{
            "role": "user",
            "content": f"""You are "the Ranger", the warm, slightly dramatic guide of GrassQuest, a game that gets people outside.
Write the player's quest briefing from these facts (JSON):
{json.dumps(facts)}

Rules:
- "title": the SAME action as the quest, stated plainly so the player knows exactly what to do. Add the real destination name if there is one. Max 80 characters.
- "briefing": 2-3 short spoken sentences to the player. Say where to go (name, direction, distance) if there's a destination, and use the weather/time.
- "tip": max 15 words on what photo to bring back.
No emojis."""
        }]
    }

    print("Generating quest briefing with Gemma 4...")
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=chat_body, timeout=60)
    dur = round(time.time() - t0, 2)
    assert r.status_code == 200, f"Chat failed: {r.status_code} {r.text}"
    content = json.loads(r.json()["message"]["content"])
    print(f"[PASS] Personalization succeeded in {dur}s:")
    print(f"  Title:    {content.get('title')}")
    print(f"  Briefing: {content.get('briefing')}")
    print(f"  Tip:      {content.get('tip')}")

    # 3. Test image judging schema
    VERDICT_SCHEMA = {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": ["pass", "close", "no"]},
            "confidence": {"type": "number"},
            "seen": {"type": "string"},
            "reaction": {"type": "string"},
            "identified": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "kind": {"type": "string", "enum": ["bird", "plant", "tree", "insect", "fungus", "sky", "animal", "none"]},
                    "fact": {"type": "string"},
                    "rarity": {"type": "string", "enum": ["common", "uncommon", "rare"]}
                },
                "required": ["name", "kind", "fact", "rarity"]
            }
        },
        "required": ["verdict", "confidence", "seen", "reaction", "identified"]
    }

    # 1x1 green pixel PNG base64 for vision test
    mock_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    t0 = time.time()
    judge_body = {
        "model": model,
        "format": VERDICT_SCHEMA,
        "options": {"temperature": 0.2},
        "think": False,
        "stream": False,
        "keep_alive": "30m",
        "messages": [{
            "role": "user",
            "images": [mock_png_b64],
            "content": """You are the friendly judge of GrassQuest, a casual game that gets people outside.
Quest: "Find a green leaf"
A good photo looks like: A clear photo of any green leaf outdoors

Decide:
- "pass": an honest photo that reasonably fits the quest.
- "close": the right idea but incomplete.
- "no": the main subject has nothing to do with the quest, a screen/screenshot, or obviously not real.
Also:
- "seen": what's in the photo, max 12 words.
- "reaction": one playful line to the player, max 22 words.
- "identified": the most interesting living thing or sky feature in the photo."""
        }]
    }

    print("Testing image judging with Gemma 4...")
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=judge_body, timeout=90)
    dur = round(time.time() - t0, 2)
    assert r.status_code == 200, f"Judge failed: {r.status_code} {r.text}"
    v = json.loads(r.json()["message"]["content"])
    print(f"[PASS] Vision judging succeeded in {dur}s:")
    print(f"  Verdict:    {v.get('verdict')} (confidence: {v.get('confidence')})")
    print(f"  Seen:       {v.get('seen')}")
    print(f"  Reaction:   {v.get('reaction')}")
    print(f"  Identified: {v.get('identified')}")
    print("=" * 60)
    print("ALL GEMMA 4 TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_gemma()
