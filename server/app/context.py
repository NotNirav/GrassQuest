"""Where is the player, what's the weather, and what's within walking distance?

Free, keyless sources:
  Open-Meteo (weather + sunrise/sunset), OpenStreetMap Overpass (nearby places), Nominatim (area name / city search).
Coordinates are rounded to a ~1 km cell before anything leaves the server or gets cached, and raw coordinates are never stored.
"""
import logging
import math
import time
from datetime import datetime, timedelta, timezone

import httpx
import sentry_sdk

from . import db

log = logging.getLogger(__name__)

UA = {"User-Agent": "GrassQuest/0.2 (hackathon project; https://github.com/NotNirav/GrassQuest)"}
RADIUS_M = 1500
WEATHER_TTL_S = 20 * 60
PLACES_TTL_S = 7 * 24 * 3600
AREA_TTL_S = 30 * 24 * 3600

# Overpass: which OSM tags count as which game feature
FEATURE_QUERIES = {
    "park": ['nwr["leisure"="park"]', 'nwr["leisure"="nature_reserve"]'],
    "garden": ['nwr["leisure"="garden"]', 'nwr["landuse"="flowerbed"]'],
    "playground": ['nwr["leisure"="playground"]'],
    "water": ['nwr["natural"="water"]', 'nwr["waterway"~"^(river|stream|canal)$"]', 'nwr["natural"="beach"]', 'nwr["amenity"="fountain"]'],
    "trees": ['nwr["natural"~"^(wood|tree_row)$"]', 'nwr["landuse"="forest"]'],
    "field": ['nwr["landuse"~"^(grass|meadow|recreation_ground|village_green)$"]', 'nwr["leisure"~"^(pitch|common)$"]'],
    "viewpoint": ['nwr["tourism"="viewpoint"]', 'nwr["natural"="peak"]'],
    "trail": ['way["highway"~"^(path|footway|track)$"]["name"]'],
    "bench": ['node["amenity"="bench"]'],
    "cafe": ['nwr["amenity"="cafe"]["outdoor_seating"="yes"]', 'nwr["amenity"="ice_cream"]'],
}
GENERIC_NAME = {
    "park": "the nearest park", "garden": "the nearest garden", "playground": "the nearest playground",
    "water": "the nearest water", "trees": "the nearest trees", "field": "the nearest patch of grass",
    "viewpoint": "the nearest viewpoint", "trail": "the nearest footpath", "bench": "the nearest bench",
    "cafe": "a café with outdoor seats",
}

WMO = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "fog", 51: "light drizzle", 53: "drizzle",
       55: "heavy drizzle", 56: "freezing drizzle", 57: "freezing drizzle", 61: "light rain", 63: "rain", 65: "heavy rain",
       66: "freezing rain", 67: "freezing rain", 71: "light snow", 73: "snow", 75: "heavy snow", 77: "snow grains",
       80: "rain showers", 81: "rain showers", 82: "violent showers", 85: "snow showers", 86: "heavy snow showers",
       95: "thunderstorm", 96: "thunderstorm with hail", 99: "thunderstorm with hail"}


def cell(lat: float, lon: float) -> tuple[float, float]:
    return round(lat, 2), round(lon, 2)


def _cached(key: str, ttl: int):
    doc = db.context_cache.find_one({"_id": key})
    if doc and time.time() - doc["at"] < ttl:
        return doc["data"]
    return None


def _store(key: str, data):
    db.context_cache.replace_one({"_id": key}, {"_id": key, "at": time.time(), "data": data}, upsert=True)


def _dist_bearing(lat1, lon1, lat2, lon2):
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    dist = 2 * r * math.asin(math.sqrt(a))
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    deg = (math.degrees(math.atan2(y, x)) + 360) % 360
    return round(dist), ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"][round(deg / 45) % 8]


# ---------- weather ----------
def weather(lat: float, lon: float) -> dict:
    clat, clon = cell(lat, lon)
    key = f"wx:{clat}:{clon}"
    hit = _cached(key, WEATHER_TTL_S)
    if hit:
        return hit
    with sentry_sdk.start_span(op="http.client", name="Open-Meteo"):
        r = httpx.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": clat, "longitude": clon, "timezone": "auto", "forecast_days": 2,
            "current": "temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,is_day",
            "hourly": "precipitation_probability,precipitation,weather_code",
            "daily": "sunrise,sunset",
        }, timeout=15)
        r.raise_for_status()
    d = r.json()
    cur = d["current"]
    code = int(cur["weather_code"])
    now_local = datetime.fromisoformat(cur["time"])
    hours = d["hourly"]["time"]
    idx = next((i for i, h in enumerate(hours) if datetime.fromisoformat(h) >= now_local), 0)
    next3 = list(zip(hours[idx:idx + 3], d["hourly"]["precipitation_probability"][idx:idx + 3], d["hourly"]["precipitation"][idx:idx + 3]))
    rain_at = next((h for h, prob, mm in next3 if (prob or 0) >= 60 and (mm or 0) >= 0.5), None)
    sunrise = datetime.fromisoformat(d["daily"]["sunrise"][0])
    sunset = datetime.fromisoformat(d["daily"]["sunset"][0])
    temp, wind, precip = cur["temperature_2m"], cur["wind_speed_10m"], cur["precipitation"]

    if code >= 95 or code in (65, 67, 75, 82, 86) or precip >= 4 or wind >= 50 or temp >= 41 or temp <= -10:
        band = "severe"
    elif code in (61, 63, 66, 80, 81, 71, 73, 77, 85) or precip >= 1:
        band = "rain"
    elif code in (51, 53, 55, 56, 57) or precip > 0:
        band = "drizzle"
    elif temp >= 35:
        band = "hot"
    elif temp <= 3:
        band = "cold"
    elif wind >= 30:
        band = "windy"
    elif code in (45, 48):
        band = "fog"
    elif code >= 2:
        band = "cloudy"
    else:
        band = "clear"

    data = {
        "temp": round(temp), "feels": round(cur["apparent_temperature"]), "wind": round(wind), "precip_mm": precip,
        "code": code, "label": WMO.get(code, "unknown"), "band": band, "is_day": bool(cur["is_day"]),
        "local_time": cur["time"], "utc_offset_s": d.get("utc_offset_seconds", 0),
        "sunrise": sunrise.isoformat(), "sunset": sunset.isoformat(),
        "rain_soon_at": rain_at,
    }
    _store(key, data)
    return data


def sun_phase(wx: dict) -> dict:
    """Derived from cached weather + the current time, so it stays fresh between weather refreshes."""
    offset = timedelta(seconds=wx["utc_offset_s"])
    now_local = datetime.now(timezone.utc).replace(tzinfo=None) + offset
    sunrise, sunset = datetime.fromisoformat(wx["sunrise"]), datetime.fromisoformat(wx["sunset"])
    to_sunset = (sunset - now_local).total_seconds() / 60
    since_sunrise = (now_local - sunrise).total_seconds() / 60
    if to_sunset < -30 or since_sunrise < -30:
        phase = "night"
    elif 0 <= since_sunrise <= 150:
        phase = "morning"
    elif -30 <= to_sunset <= 90:
        phase = "golden"
    else:
        phase = "day"
    return {"phase": phase, "minutes_to_sunset": round(to_sunset), "local_hour": now_local.hour, "local_dow": now_local.weekday(),
            "local_date": now_local.date().isoformat()}


# ---------- places ----------
def places(lat: float, lon: float) -> dict:
    clat, clon = cell(lat, lon)
    key = f"pl:{clat}:{clon}"
    hit = _cached(key, PLACES_TTL_S)
    if hit is not None:
        return hit
    parts = []
    for feature, qs in FEATURE_QUERIES.items():
        for q in qs:
            parts.append(f'{q}(around:{RADIUS_M},{clat},{clon});')
    query = f"[out:json][timeout:25];({''.join(parts)});out center tags 400;"
    try:
        with sentry_sdk.start_span(op="http.client", name="Overpass"):
            r = httpx.post("https://overpass-api.de/api/interpreter", data={"data": query}, headers=UA, timeout=30)
            r.raise_for_status()
        elements = r.json().get("elements", [])
    except Exception:
        log.warning("Overpass failed; continuing with street and sky quests only", exc_info=True)
        return {}

    best: dict[str, dict] = {}
    for el in elements:
        tags = el.get("tags", {})
        plat = el.get("lat") or el.get("center", {}).get("lat")
        plon = el.get("lon") or el.get("center", {}).get("lon")
        if plat is None:
            continue
        feature = _classify(tags)
        if not feature:
            continue
        dist, bearing = _dist_bearing(clat, clon, plat, plon)
        name = tags.get("name") or tags.get("name:en")
        cand = {"name": name, "dist_m": dist, "bearing": bearing, "lat": round(plat, 4), "lon": round(plon, 4)}
        cur = best.get(feature)
        # prefer named places, then closer ones
        if cur is None or (bool(name), -dist) > (bool(cur["name"]), -cur["dist_m"]):
            best[feature] = cand
    # parks have trees and grass even when OSM doesn't tag them separately
    if "park" in best:
        best.setdefault("trees", {**best["park"]})
        best.setdefault("field", {**best["park"]})
        best.setdefault("bench", {**best["park"]})
    _store(key, best)
    return best


def _classify(tags: dict) -> str | None:
    leisure, natural, landuse = tags.get("leisure"), tags.get("natural"), tags.get("landuse")
    if leisure in ("park", "nature_reserve"):
        return "park"
    if leisure == "garden" or landuse == "flowerbed":
        return "garden"
    if leisure == "playground":
        return "playground"
    if natural in ("water", "beach") or tags.get("waterway") in ("river", "stream", "canal") or tags.get("amenity") == "fountain":
        return "water"
    if natural in ("wood", "tree_row") or landuse == "forest":
        return "trees"
    if landuse in ("grass", "meadow", "recreation_ground", "village_green") or leisure in ("pitch", "common"):
        return "field"
    if tags.get("tourism") == "viewpoint" or natural == "peak":
        return "viewpoint"
    if tags.get("highway") in ("path", "footway", "track"):
        return "trail"
    if tags.get("amenity") == "bench":
        return "bench"
    if tags.get("amenity") in ("cafe", "ice_cream"):
        return "cafe"
    return None


# ---------- area name ----------
def area(lat: float, lon: float) -> dict:
    clat, clon = cell(lat, lon)
    key = f"ar:{clat}:{clon}"
    hit = _cached(key, AREA_TTL_S)
    if hit:
        return hit
    try:
        r = httpx.get("https://nominatim.openstreetmap.org/reverse", params={"format": "jsonv2", "lat": clat, "lon": clon, "zoom": 14},
                      headers=UA, timeout=15)
        a = r.json().get("address", {})
        data = {
            "name": a.get("suburb") or a.get("neighbourhood") or a.get("city_district") or a.get("town") or a.get("village") or a.get("city"),
            "city": a.get("city") or a.get("town") or a.get("village") or a.get("county") or a.get("state"),
            "country": a.get("country_code", "").upper(),
        }
    except Exception:
        data = {"name": None, "city": None, "country": ""}
    _store(key, data)
    return data


def search_city(q: str) -> list[dict]:
    r = httpx.get("https://nominatim.openstreetmap.org/search", params={"format": "jsonv2", "q": q, "limit": 5},
                  headers=UA, timeout=15)
    return [{"label": x["display_name"], "lat": round(float(x["lat"]), 2), "lon": round(float(x["lon"]), 2)} for x in r.json()]


def build(lat: float, lon: float) -> dict:
    clat, clon = cell(lat, lon)
    wx = weather(clat, clon)
    pl = places(clat, clon)
    return {
        "cell": [clat, clon],
        "area": area(clat, clon),
        "weather": wx,
        "sun": sun_phase(wx),
        "places": pl,
        "features": sorted(set(pl) | {"street", "sky"}),
    }


def place_for(ctx: dict, needs: list[str]) -> dict | None:
    """The real place a quest should send the player to (its first need)."""
    for n in needs:
        p = ctx["places"].get(n)
        if p:
            return {"feature": n, "name": p["name"] or GENERIC_NAME.get(n, "a spot nearby"), "named": bool(p["name"]),
                    "dist_m": p["dist_m"], "bearing": p["bearing"], "lat": p["lat"], "lon": p["lon"]}
    return None
