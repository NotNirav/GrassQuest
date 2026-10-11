"""Live end-to-end API test suite for GrassQuest.
Tests against the live running server (http://127.0.0.1:8000) or directly against the app.
"""
import uuid
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def log_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}{': ' + detail if detail else ''}")
    return passed

def run_tests():
    total = 0
    passed = 0

    print("=" * 60)
    print("GRASSQUEST LIVE BACKEND TEST SUITE")
    print(f"Target: {BASE_URL}")
    print("=" * 60)

    # 1. Health check
    total += 1
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=5)
        data = r.json()
        ok = r.status_code == 200 and data.get("ok") is True and data.get("quests", 0) > 0
        detail = f"status={r.status_code}, db={data.get('db')}, quests={data.get('quests')}, templates={data.get('templates')}"
        if log_test("Health check (/api/health)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Health check (/api/health)", False, str(e))

    # 2. Badges catalog
    total += 1
    try:
        r = requests.get(f"{BASE_URL}/api/badges", timeout=5)
        badges = r.json()
        ok = r.status_code == 200 and len(badges) >= 12
        detail = f"{len(badges)} badges defined"
        if log_test("Badges catalog (/api/badges)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Badges catalog (/api/badges)", False, str(e))

    # 3. Reverse geocode
    total += 1
    try:
        r = requests.get(f"{BASE_URL}/api/reverse", params={"lat": 18.59, "lon": 73.79}, timeout=10)
        data = r.json()
        ok = r.status_code == 200 and "title" in data
        detail = f"title='{data.get('title')}', detail='{data.get('detail')}'"
        if log_test("Reverse geocoding (/api/reverse)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Reverse geocoding (/api/reverse)", False, str(e))

    # 4. Geocode search
    total += 1
    try:
        r = requests.get(f"{BASE_URL}/api/geocode", params={"q": "Pimple Saudagar"}, timeout=10)
        data = r.json()
        ok = r.status_code == 200 and isinstance(data, list)
        detail = f"found {len(data)} results"
        if log_test("Geocode search (/api/geocode)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Geocode search (/api/geocode)", False, str(e))

    # 5. Context fetch (Weather + Places)
    total += 1
    lat, lon = 18.59, 73.79
    try:
        r = requests.post(f"{BASE_URL}/api/context", json={"lat": lat, "lon": lon}, timeout=15)
        ctx = r.json()
        ok = (r.status_code == 200 and "weather" in ctx and "sun" in ctx and "features" in ctx)
        detail = f"weather={ctx.get('weather', {}).get('band')} ({ctx.get('weather', {}).get('temp')}°C), sun={ctx.get('sun', {}).get('phase')}, features={len(ctx.get('features', []))}"
        if log_test("World context (/api/context)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("World context (/api/context)", False, str(e))

    # 6. User creation & constraints
    total += 1
    test_handle = f"Test_{uuid.uuid4().hex[:6]}"
    user = None
    try:
        # Invalid handle (too short)
        r_short = requests.post(f"{BASE_URL}/api/users", json={"handle": "a"}, timeout=5)
        # Valid handle
        r = requests.post(f"{BASE_URL}/api/users", json={"handle": test_handle}, timeout=5)
        user = r.json()
        # Duplicate handle
        r_dup = requests.post(f"{BASE_URL}/api/users", json={"handle": test_handle}, timeout=5)
        
        ok = (r_short.status_code == 422 and r.status_code == 200 and r_dup.status_code == 409
              and user.get("handle") == test_handle and user.get("level") == 1 and user.get("xp") == 0)
        detail = f"handle='{test_handle}', id={user.get('id')}, dup_status={r_dup.status_code}"
        if log_test("User creation & constraints (/api/users)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("User creation & constraints (/api/users)", False, str(e))

    if not user or not user.get("id"):
        print("Aborting remaining tests because user creation failed.")
        return passed, total

    user_id = user["id"]

    # 7. Read user
    total += 1
    try:
        r = requests.get(f"{BASE_URL}/api/users/{user_id}", params={"today": "2026-10-11"}, timeout=5)
        u_data = r.json()
        ok = r.status_code == 200 and u_data.get("id") == user_id
        detail = f"handle={u_data.get('handle')}, streak={u_data.get('streak')}"
        if log_test("Read user profile (/api/users/{id})", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Read user profile (/api/users/{id})", False, str(e))

    # 8. Quests today
    total += 1
    offers_data = None
    try:
        r = requests.post(f"{BASE_URL}/api/quests/today", json={"user_id": user_id, "lat": lat, "lon": lon, "exclude": []}, timeout=20)
        offers_data = r.json()
        choices = offers_data.get("choices", [])
        slots = [c["slot"] for c in choices]
        ok = r.status_code == 200 and len(choices) >= 1 and "context" in offers_data
        detail = f"{len(choices)} choices: {slots}, p_complete={[round(c['p'], 2) for c in choices]}, mins={[c['minutes'] for c in choices]}"
        if log_test("Quests today (/api/quests/today)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Quests today (/api/quests/today)", False, str(e))

    if not offers_data or not offers_data.get("choices"):
        print("Aborting quest flow tests because no choices returned.")
        return passed, total

    choice = offers_data["choices"][0]
    offer_id = choice["offer_id"]

    # 9. Accept quest offer
    total += 1
    try:
        r = requests.post(f"{BASE_URL}/api/offers/{offer_id}/accept", timeout=5)
        res = r.json()
        ok = r.status_code == 200 and res.get("ok") is True
        detail = f"offer_id={offer_id}, accepted=True"
        if log_test("Accept quest offer (/api/offers/{id}/accept)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Accept quest offer (/api/offers/{id}/accept)", False, str(e))

    # 10. Submit verdict 'no' (failure case)
    total += 1
    try:
        r = requests.post(f"{BASE_URL}/api/offers/{offer_id}/verdict", json={
            "verdict": "no",
            "confidence": 0.95,
            "seen": "A blank screen",
            "reaction": "Go outside and take a real photo!",
            "model": "test-suite"
        }, timeout=5)
        res = r.json()
        ok = r.status_code == 200 and res.get("verdict") == "no" and res.get("fails") == 1
        detail = f"verdict={res.get('verdict')}, fails={res.get('fails')}"
        if log_test("Verdict 'no' handling (/api/offers/{id}/verdict)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Verdict 'no' handling (/api/offers/{id}/verdict)", False, str(e))

    # 11. Submit verdict 'pass' with species identification
    total += 1
    verdict_pass_res = None
    try:
        r = requests.post(f"{BASE_URL}/api/offers/{offer_id}/verdict", json={
            "verdict": "pass",
            "confidence": 0.98,
            "seen": "A vibrant green neem leaf",
            "reaction": "Splendid observation!",
            "identified": {
                "kind": "tree",
                "name": "Neem Tree",
                "fact": "Neem twigs have natural antibacterial properties.",
                "rarity": "common"
            },
            "model": "test-suite"
        }, timeout=5)
        verdict_pass_res = r.json()
        xp = verdict_pass_res.get("xp", 0)
        seeds = verdict_pass_res.get("seeds", 0)
        new_card = verdict_pass_res.get("new_card")
        p_updated = verdict_pass_res.get("player", {})
        ok = (r.status_code == 200 and verdict_pass_res.get("verdict") == "pass"
              and xp > 0 and seeds > 0 and new_card is not None and new_card.get("kind") == "tree"
              and p_updated.get("completed") == 1 and p_updated.get("streak") == 1)
        detail = f"awarded XP={xp}, Seeds={seeds}, card='{new_card.get('name') if new_card else None}', new_streak={p_updated.get('streak')}"
        if log_test("Verdict 'pass' with Field Guide entry", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Verdict 'pass' with Field Guide entry", False, str(e))

    # 12. Prevent duplicate verdict on finished quest
    total += 1
    try:
        r = requests.post(f"{BASE_URL}/api/offers/{offer_id}/verdict", json={
            "verdict": "pass", "confidence": 1.0, "seen": "", "reaction": "", "model": "test"
        }, timeout=5)
        ok = r.status_code == 409
        detail = f"status={r.status_code} (correctly rejected already finished quest)"
        if log_test("Prevent duplicate completion on finished offer", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Prevent duplicate completion on finished offer", False, str(e))

    # 13. Economy: Basecamp upgrade
    total += 1
    try:
        # Give user enough seeds to buy shelter upgrade (tent costs 40 seeds)
        # Check buy endpoint
        r = requests.post(f"{BASE_URL}/api/camp/buy", json={"user_id": user_id, "slot": "shelter", "today": "2026-10-11"}, timeout=5)
        # User might have insufficient seeds or sufficient seeds
        if r.status_code == 409 and "need" in r.text.lower():
            ok = True
            detail = f"correctly rejected purchase with insufficient seeds: {r.json().get('detail')}"
        elif r.status_code == 200:
            ok = True
            detail = f"successfully upgraded shelter"
        else:
            ok = False
            detail = f"unexpected response: {r.status_code} {r.text}"
        if log_test("Basecamp purchase validation (/api/camp/buy)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Basecamp purchase validation (/api/camp/buy)", False, str(e))

    # 14. Economy: Streak Freeze purchase validation
    total += 1
    try:
        r = requests.post(f"{BASE_URL}/api/freeze/buy", json={"user_id": user_id, "today": "2026-10-11"}, timeout=5)
        if r.status_code == 409 and "cost" in r.text.lower():
            ok = True
            detail = f"correctly enforced seeds requirement for streak freeze"
        elif r.status_code == 200:
            ok = True
            detail = "purchased streak freeze"
        else:
            ok = False
            detail = f"unexpected response: {r.status_code} {r.text}"
        if log_test("Streak freeze purchase validation (/api/freeze/buy)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Streak freeze purchase validation (/api/freeze/buy)", False, str(e))

    # 15. Leaderboard (week, all, area)
    total += 1
    try:
        r_week = requests.get(f"{BASE_URL}/api/leaderboard", params={"scope": "week", "today": "2026-10-11"}, timeout=5)
        r_all = requests.get(f"{BASE_URL}/api/leaderboard", params={"scope": "all"}, timeout=5)
        ok = r_week.status_code == 200 and r_all.status_code == 200 and isinstance(r_week.json(), list)
        detail = f"week_entries={len(r_week.json())}, all_entries={len(r_all.json())}"
        if log_test("Leaderboard retrieval (/api/leaderboard)", ok, detail):
            passed += 1
    except Exception as e:
        log_test("Leaderboard retrieval (/api/leaderboard)", False, str(e))

    # Clean up test user
    try:
        from app import db
        db.users.delete_one({"_id": user_id})
        db.attempts.delete_many({"user_id": user_id})
        print(f"[CLEANUP] Deleted test user {user_id} and test attempts.")
    except Exception as e:
        print(f"[CLEANUP] Failed to cleanup: {e}")

    print("=" * 60)
    print(f"RESULTS: {passed}/{total} tests passed ({round(passed/total*100, 1)}%)")
    print("=" * 60)
    return passed, total

if __name__ == "__main__":
    passed, total = run_tests()
    sys.exit(0 if passed == total else 1)
