"""Keeps TabPFN inside the free tier.

Free tier (checked 2026-10-10 against our own account): 5M tokens/day (resets 00:00 UTC), 20M/month (resets on the 1st).
Each predict call costs a flat 10k tokens at our data size (the per-call minimum).

We stop well before the real limits: hosted defaults are 75% (3.75M/day, 15M/month); local .env uses 50%.
Usage = max(what Prior Labs reports, our own Mongo ledger), so several app instances share one budget.
"""
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from . import config, db

log = logging.getLogger(__name__)

COST_PER_CALL = 10_000
SERVER_REFRESH_S = 300

_lock = threading.Lock()
_server = {"daily": 0, "monthly": 0, "checked_at": 0.0}
_pause = {"until": None, "reason": ""}
_minute = {"window": 0, "calls": 0}


def _now():
    return datetime.now(timezone.utc)


def _keys(now):
    return now.strftime("%Y-%m-%d"), now.strftime("%Y-%m")


def _next_day(now):
    return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)


def _next_month(now):
    return (now.replace(day=28) + timedelta(days=4)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _ledger(now) -> tuple[int, int]:
    day, month = _keys(now)
    d = db.tabpfn_usage.find_one({"_id": f"day:{day}"}) or {}
    m = db.tabpfn_usage.find_one({"_id": f"month:{month}"}) or {}
    return d.get("tokens", 0), m.get("tokens", 0)


def _refresh_server_usage():
    if time.time() - _server["checked_at"] < SERVER_REFRESH_S:
        return
    _server["checked_at"] = time.time()
    try:
        from tabpfn_client.client import ServiceClient

        u = ServiceClient.get_api_usage(config.TABPFN_TOKEN)
        _server.update(daily=int(u.get("daily_tokens_used", 0)), monthly=int(u.get("monthly_tokens_used", 0)))
    except Exception:
        log.warning("Couldn't read TabPFN usage from Prior Labs; using our own ledger only", exc_info=True)


def usage() -> dict:
    now = _now()
    ledger_day, ledger_month = _ledger(now)
    return {
        "daily_used": max(_server["daily"], ledger_day),
        "monthly_used": max(_server["monthly"], ledger_month),
        "daily_cap": config.TABPFN_DAILY_CAP,
        "monthly_cap": config.TABPFN_MONTHLY_CAP,
    }


def pause(reason: str, until: datetime):
    _pause.update(until=until, reason=reason)
    log.warning("TabPFN paused until %s: %s", until.isoformat(), reason)


def allow(user_id: str) -> tuple[bool, str]:
    """May we spend one more TabPFN call right now? Returns (ok, reason-if-not)."""
    if not config.TABPFN_TOKEN:
        return False, "not configured"
    now = _now()
    with _lock:
        if _pause["until"] and now < _pause["until"]:
            return False, _pause["reason"]
        _pause.update(until=None, reason="")

        window = int(time.time() // 60)
        if _minute["window"] != window:
            _minute.update(window=window, calls=0)
        if _minute["calls"] >= config.TABPFN_MAX_CALLS_PER_MINUTE:
            return False, "busy: site-wide rate limit"

        day, _ = _keys(now)
        user_calls = db.tabpfn_usage.find_one({"_id": f"user:{user_id}:{day}"}) or {}
        if user_calls.get("calls", 0) >= config.TABPFN_MAX_CALLS_PER_USER_DAY:
            return False, "daily limit for this player"

        _refresh_server_usage()
        u = usage()
        if u["monthly_used"] + COST_PER_CALL > u["monthly_cap"]:
            pause("monthly free-tier budget reached", _next_month(now))
            return False, _pause["reason"]
        if u["daily_used"] + COST_PER_CALL > u["daily_cap"]:
            pause("daily free-tier budget reached", _next_day(now))
            return False, _pause["reason"]

        _minute["calls"] += 1
        return True, ""


def record(user_id: str):
    """Call after a successful predict."""
    now = _now()
    day, month = _keys(now)
    db.tabpfn_usage.update_one({"_id": f"day:{day}"}, {"$inc": {"tokens": COST_PER_CALL, "calls": 1}}, upsert=True)
    db.tabpfn_usage.update_one({"_id": f"month:{month}"}, {"$inc": {"tokens": COST_PER_CALL, "calls": 1}}, upsert=True)
    db.tabpfn_usage.update_one({"_id": f"user:{user_id}:{day}"}, {"$inc": {"calls": 1}}, upsert=True)


def on_error(err: Exception):
    """A 429 from Prior Labs means a real limit was hit: stop until the next daily reset."""
    if "429" in str(err) or "rate limit" in str(err).lower() or "quota" in str(err).lower():
        pause("Prior Labs returned 429 (limit reached)", _next_day(_now()))


def status() -> dict:
    return {**usage(), "paused_until": _pause["until"].isoformat() if _pause["until"] else None,
            "pause_reason": _pause["reason"], "cost_per_call": COST_PER_CALL}
