"""SYNTHETIC history so TabPFN has something to learn from on day one. Every row is stored with synthetic=True,
excluded from leaderboards, and the write-up says so.

  python -m scripts.seed synthetic      (run from server/)
"""
import math
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone

from app import db, difficulty


def fake_context(rng):
    hour = rng.randint(5, 22)
    temp = rng.choice([rng.uniform(8, 18), rng.uniform(18, 30), rng.uniform(30, 40)])
    precip = rng.choice([0, 0, 0, 0, rng.uniform(0.1, 1), rng.uniform(1, 5)])
    band = "rain" if precip >= 1 else "drizzle" if precip > 0 else "hot" if temp >= 35 else "clear"
    return {
        "weather": {"temp": round(temp), "precip_mm": round(precip, 1), "wind": rng.randint(0, 35), "band": band},
        "sun": {"local_hour": hour, "local_dow": rng.randint(0, 6), "minutes_to_sunset": (18 - hour) * 60 + rng.randint(-30, 30)},
    }


def cmd_synthetic(n: int = 600):
    rng = random.Random(42)
    pool = list(db.quests.find({}, {"embedding": 0}))
    rows = []
    for i in range(n):
        q = rng.choice(pool)
        ctx = fake_context(rng)
        stats = {"attempts": rng.randint(0, 40), "pass_rate": round(rng.uniform(0.3, 0.9), 3)}
        streak = rng.randint(0, 10)
        dist = rng.choice([0, 0, rng.randint(100, 600), rng.randint(600, 1500)]) if q["needs"] else 0
        p = difficulty.heuristic(q, {"weather": ctx["weather"]}, stats, dist)
        p = min(0.97, p + 0.015 * min(streak, 6) + (0.06 if ctx["sun"]["local_dow"] >= 5 else 0)
                - (0.1 if ctx["sun"]["local_hour"] >= 21 and q["cat"] not in ("sky", "mindful", "rain") else 0))
        outcome = "pass" if rng.random() < p else rng.choice(["fail", "skip", "skip"])
        minutes = difficulty.heuristic_minutes(q, dist) * math.exp(rng.gauss(0, 0.35)) if outcome == "pass" else None
        feats = difficulty.feature_row(q, ctx, streak, stats, dist)
        rows.append({
            "_id": f"synthetic-{uuid.uuid4().hex}", "user_id": f"synthetic-user-{i % 20}", "quest_id": q["_id"],
            "template_id": q["template_id"], "cat": q["cat"], "rarity": q["rarity"], "outcome": outcome, "accepted": True,
            "fails": 0, "p_complete": p, "features": dict(zip(difficulty.FEATURES, feats)),
            "duration_min": round(minutes, 1) if minutes else None, "synthetic": True,
            "local_date": (date.today() - timedelta(days=rng.randint(8, 40))).isoformat(),
            "created_at": datetime.now(timezone.utc) - timedelta(days=30),
        })
    db.attempts.delete_many({"synthetic": True})
    db.attempts.insert_many(rows)
    print(f"inserted {len(rows)} SYNTHETIC rows ({sum(r['outcome'] == 'pass' for r in rows)} passes)")


if __name__ == "__main__":
    {"synthetic": cmd_synthetic}[sys.argv[1]]()
