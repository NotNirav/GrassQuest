"""XP, Seeds, levels, streaks (with freezes), Basecamp, Field Guide and badges. Pure functions where possible."""
import math
import re
from datetime import date

BASE_XP = {"common": 50, "rare": 120, "legendary": 300}
BASE_SEEDS = {1: 8, 2: 12, 3: 20, 4: 35, 5: 60}
FIELD_CARD_SEEDS = {"common": 5, "uncommon": 15, "rare": 40}
CLOSE_ENOUGH = 0.5  # "close enough" verdict pays half
FREEZE_PRICE = 40
MAX_FREEZES = 2

LEVEL_TITLES = [
    "Couch Potato", "Window Watcher", "Porch Sitter", "Sidewalk Scout", "Park Ranger",
    "Trail Blazer", "Grass Toucher", "Wild Wanderer", "Sky Reader", "Forest Sage", "Legend of the Outside",
]


# ---------- rewards ----------
def xp_multiplier(p: float) -> float:
    """Quests that are unlikely for *you* pay more: p=1 -> 0.75x, p=0 -> 2.0x."""
    p = min(max(p, 0.0), 1.0)
    return round(0.75 + 1.25 * (1 - p), 2)


def streak_multiplier(streak: int) -> float:
    """Seeds grow with your streak: +10% per day, max +100%."""
    return round(1 + 0.1 * min(streak, 10), 2)


def quest_rewards(q: dict, p: float, streak: int) -> dict:
    return {
        "xp": round(BASE_XP[q["rarity"]] * xp_multiplier(p)),
        "seeds": round(BASE_SEEDS[q["effort"]] * streak_multiplier(streak)),
        "xp_multiplier": xp_multiplier(p),
        "seed_multiplier": streak_multiplier(streak),
    }


def level_for(xp: int) -> int:
    return int(math.sqrt(max(xp, 0) / 100)) + 1  # L2 at 100 XP, L3 at 400, L4 at 900 ...


def level_info(xp: int) -> dict:
    lvl = level_for(xp)
    return {"level": lvl, "title": LEVEL_TITLES[min(lvl - 1, len(LEVEL_TITLES) - 1)], "xp": xp,
            "level_floor": 100 * (lvl - 1) ** 2, "next_level_at": 100 * lvl ** 2}


# ---------- streaks ----------
def settle_streak(user: dict, today: str) -> dict:
    """Spend freezes to cover missed days. Returns the fields to $set (may be empty)."""
    last = user.get("last_active_date")
    if not last or not user.get("streak"):
        return {}
    missed = (date.fromisoformat(today) - date.fromisoformat(last)).days - 1
    if missed <= 0:
        return {}
    freezes = user.get("freezes", 0)
    if missed <= freezes:
        # pretend the player was active yesterday; the streak survives, freezes are spent
        yesterday = date.fromordinal(date.fromisoformat(today).toordinal() - 1).isoformat()
        return {"freezes": freezes - missed, "last_active_date": yesterday, "freezes_used": user.get("freezes_used", 0) + missed}
    return {"streak": 0}


def live_streak(user: dict, today: str) -> int:
    last = user.get("last_active_date")
    if not last:
        return 0
    gap = (date.fromisoformat(today) - date.fromisoformat(last)).days
    return user.get("streak", 0) if gap <= 1 else 0


def next_streak(current: int, last_active: str | None, today: str) -> int:
    if last_active == today:
        return max(current, 1)
    if last_active and (date.fromisoformat(today) - date.fromisoformat(last_active)).days == 1:
        return current + 1
    return 1


# ---------- Basecamp ----------
CAMP = {
    "shelter": {"name": "Shelter", "tiers": [("Bedroll", 0), ("Tent", 40), ("Cabin", 150), ("Treehouse", 400)]},
    "fire": {"name": "Fire", "tiers": [("Cold ashes", 0), ("Campfire", 25), ("Stone fire pit", 90), ("Bonfire", 250)]},
    "light": {"name": "Light", "tiers": [("Nothing", 0), ("Lantern", 30), ("String lights", 100), ("Lighthouse lamp", 300)]},
    "flag": {"name": "Flag", "tiers": [("Bare pole", 0), ("Pennant", 20), ("Banner", 80), ("Summit flag", 220)]},
    "companion": {"name": "Companion", "tiers": [("Nobody", 0), ("Snail", 35), ("Fox", 160), ("Owl", 450)]},
    "gear": {"name": "Gear", "tiers": [("Nothing", 0), ("Backpack", 30), ("Binoculars", 110), ("Telescope", 320)]},
}


def camp_view(camp: dict) -> list[dict]:
    out = []
    for slot, spec in CAMP.items():
        tier = camp.get(slot, 0)
        nxt = spec["tiers"][tier + 1] if tier + 1 < len(spec["tiers"]) else None
        out.append({"slot": slot, "name": spec["name"], "tier": tier, "item": spec["tiers"][tier][0], "max_tier": len(spec["tiers"]) - 1,
                    "next": {"item": nxt[0], "price": nxt[1]} if nxt else None})
    return out


# ---------- Field Guide ----------
KINDS = {"bird", "plant", "tree", "insect", "fungus", "sky", "animal"}


def card_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60]


# ---------- badges ----------
BADGES = {
    "first-steps": ("First Steps", "Complete your first quest", "👣"),
    "early-bird": ("Early Bird", "Complete a quest before 7 AM", "🌅"),
    "night-owl": ("Night Owl", "Complete a quest after 9 PM", "🦉"),
    "golden-hour": ("Golden Hour Hunter", "Complete a quest in the hour before sunset", "🌇"),
    "monsoon": ("Monsoon Walker", "Complete a quest in the rain", "🌧️"),
    "heatwave": ("Heat Proof", "Complete a quest above 32°C", "🥵"),
    "naturalist": ("Naturalist", "Collect 10 Field Guide cards", "📔"),
    "birder": ("Birder", "Collect 5 different birds", "🐦"),
    "streak-3": ("On a Roll", "Reach a 3-day streak", "🔥"),
    "streak-7": ("Unstoppable", "Reach a 7-day streak", "☄️"),
    "legend": ("Legendary", "Complete a legendary quest", "🏆"),
    "underdog": ("Underdog", "Finish a quest you had under 30% odds on", "🎯"),
    "homesteader": ("Homesteader", "Upgrade every Basecamp slot at least once", "🏕️"),
    "explorer": ("Far Walker", "Complete a quest at a place over 1 km away", "🧭"),
}


def earned_badges(user: dict, q: dict, offer: dict, ctx_weather: dict | None) -> list[str]:
    have = set(user.get("badges", []))
    hour = offer["features"]["hour"]
    new = []

    def award(key, cond):
        if cond and key not in have and key not in new:
            new.append(key)

    guide = user.get("field_guide", {})
    award("first-steps", True)
    award("early-bird", hour < 7)
    award("night-owl", hour >= 21)
    award("golden-hour", 0 <= offer["features"]["minutes_to_sunset"] <= 60)
    award("monsoon", (ctx_weather or {}).get("band") in ("rain", "drizzle"))
    award("heatwave", offer["features"]["temp"] >= 32)
    award("naturalist", len(guide) >= 10)
    award("birder", sum(1 for c in guide.values() if c["kind"] == "bird") >= 5)
    award("streak-3", user.get("streak", 0) >= 3)
    award("streak-7", user.get("streak", 0) >= 7)
    award("legend", q["rarity"] == "legendary")
    award("underdog", offer["p_complete"] < 0.3)
    award("explorer", offer["features"]["dist_m"] >= 1000)
    return new


def badge_view(key: str) -> dict:
    name, desc, icon = BADGES[key]
    return {"key": key, "name": name, "description": desc, "icon": icon}
