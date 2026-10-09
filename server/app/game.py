"""XP, levels, streaks and badges. Pure functions so they're easy to test."""
import math
from datetime import date, timedelta

BASE_XP = {"common": 50, "rare": 120, "legendary": 300, "boss": 500}

LEVEL_TITLES = [
    "Couch Potato", "Window Watcher", "Porch Sitter", "Sidewalk Scout", "Park Ranger",
    "Trail Blazer", "Grass Toucher", "Wild Wanderer", "Sky Reader", "Forest Sage", "Legend of the Outside",
]


def xp_multiplier(p_complete: float) -> float:
    """Quests that are unlikely for *you* pay more: p=1 -> 0.75x, p=0 -> 2.0x."""
    p = min(max(p_complete, 0.0), 1.0)
    return round(0.75 + 1.25 * (1 - p), 2)


def streak_bonus(streak: int) -> float:
    """+5% per streak day, capped at +50%."""
    return min(streak, 10) * 0.05


def quest_xp(rarity: str, p_complete: float, streak: int) -> int:
    return round(BASE_XP[rarity] * xp_multiplier(p_complete) * (1 + streak_bonus(streak)))


def level_for(xp: int) -> int:
    # L2 at 100 XP, L3 at 400, L4 at 900, ... (100 * (L-1)^2)
    return int(math.sqrt(max(xp, 0) / 100)) + 1


def level_info(xp: int) -> dict:
    lvl = level_for(xp)
    floor_xp, next_xp = 100 * (lvl - 1) ** 2, 100 * lvl ** 2
    return {
        "level": lvl,
        "title": LEVEL_TITLES[min(lvl - 1, len(LEVEL_TITLES) - 1)],
        "xp": xp,
        "level_floor": floor_xp,
        "next_level_at": next_xp,
    }


def next_streak(current: int, last_active: str | None, today: str) -> int:
    """Streak counts consecutive local days with at least one completed quest."""
    if last_active == today:
        return current
    if last_active and date.fromisoformat(today) - date.fromisoformat(last_active) == timedelta(days=1):
        return current + 1
    return 1


def live_streak(user: dict, today: str) -> int:
    """Streak as displayed today: it only breaks once a full day has been missed."""
    last = user.get("last_active_date")
    if not last:
        return 0
    gap = (date.fromisoformat(today) - date.fromisoformat(last)).days
    return user.get("streak", 0) if gap <= 1 else 0


BADGES = {
    "first-steps": ("First Steps", "Complete your first quest", "👣"),
    "early-bird": ("Early Bird", "Complete a quest before 7 AM", "🌅"),
    "night-owl": ("Night Owl", "Complete a quest after 9 PM", "🦉"),
    "botanist": ("Botanist", "Complete 10 plant quests", "🌿"),
    "birdwatcher": ("Birdwatcher", "Complete 5 bird quests", "🐦"),
    "sky-gazer": ("Sky Gazer", "Complete 5 sky quests", "☁️"),
    "water-sign": ("Water Sign", "Complete 5 water quests", "💧"),
    "streak-3": ("On a Roll", "Reach a 3-day streak", "🔥"),
    "streak-7": ("Unstoppable", "Reach a 7-day streak", "☄️"),
    "legend": ("Legendary", "Complete a legendary quest", "🏆"),
    "boss-slayer": ("Boss Slayer", "Beat a weekly boss quest", "🐉"),
    "underdog": ("Underdog", "Complete a quest you had under 30% odds of finishing", "🎯"),
}

CATEGORY_BADGES = {"plants": ("botanist", 10), "birds": ("birdwatcher", 5), "sky": ("sky-gazer", 5), "water": ("water-sign", 5)}


def earned_badges(user: dict, quest: dict, hour: int, p_complete: float) -> list[str]:
    """Badges newly earned by this completion. `user` already has updated counts/streak."""
    have = set(user.get("badges", []))
    new = []

    def award(key, cond):
        if cond and key not in have:
            new.append(key)

    award("first-steps", True)
    award("early-bird", hour < 7)
    award("night-owl", hour >= 21)
    if quest["category"] in CATEGORY_BADGES:
        key, need = CATEGORY_BADGES[quest["category"]]
        award(key, user.get("counts", {}).get(quest["category"], 0) >= need)
    award("streak-3", user.get("streak", 0) >= 3)
    award("streak-7", user.get("streak", 0) >= 7)
    award("legend", quest["rarity"] == "legendary")
    award("boss-slayer", quest["rarity"] == "boss")
    award("underdog", p_complete < 0.3)
    return new


def badge_view(key: str) -> dict:
    name, desc, icon = BADGES[key]
    return {"key": key, "name": name, "description": desc, "icon": icon}
