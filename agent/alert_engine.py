"""
alert_engine.py — Fresh Events Engine for Hyderabad Opportunity Scout
Ensures users see DIFFERENT events every day via disk-persisted hashing.
"""
import hashlib
import json
import os
import random
import logging
from datetime import date, datetime

logger = logging.getLogger(__name__)

SEEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".seen_events.json")


# ─────────────────────────────── PERSISTENCE ────────────────────────────────

def load_seen_registry() -> dict:
    try:
        with open(SEEN_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_seen_registry(data: dict):
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save seen registry: {e}")


def clear_seen_registry():
    save_seen_registry({})


# ─────────────────────────────── HASHING ────────────────────────────────────

def make_hash(event: dict) -> str:
    """Create a stable 12-char hash from event name + date."""
    name = event.get("title", event.get("name", "")).lower().strip()
    date_str = event.get("reg_deadline", event.get("date", "")).strip()
    raw = f"{name}|{date_str}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ─────────────────────────────── DATE UTILS ─────────────────────────────────

def days_until(date_str: str):
    """Parse a date string and return days until that date. Returns None on failure."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%B %d, %Y", "%d %B %Y", "%Y/%m/%d"):
        try:
            parsed = datetime.strptime(date_str.strip(), fmt).date()
            return (parsed - date.today()).days
        except ValueError:
            continue
    return None


# ─────────────────────────────── SCORING ────────────────────────────────────

def score(event: dict, day_index: int) -> float:
    """Score an event for selection priority on a given weekday."""
    s = 0.0
    preferred_sources = ["Unstop", "Commudle", "Meetup"]
    source = event.get("source", "")
    if preferred_sources[day_index % 3].lower() in source.lower():
        s += 30

    fee = int(event.get("price", event.get("fee", 0)) or 0)
    if fee == 0:
        s += 25
    elif fee <= 50:
        s += 15
    elif fee <= 100:
        s += 8

    days_away = days_until(event.get("reg_deadline", event.get("date", "")))
    if days_away is not None:
        if 0 <= days_away <= 7:
            s += 20
        elif days_away <= 14:
            s += 10

    s += random.uniform(0, 5)  # shuffle equal scores
    return s


# ─────────────────────────────── MAIN LOGIC ─────────────────────────────────

def get_fresh_events(all_events: list, count: int = 5) -> list:
    """
    Returns `count` events the user hasn't seen, or seen 7+ days ago.
    Falls back to full reset if nothing fresh.
    """
    seen = load_seen_registry()
    today = date.today()

    unseen = []
    seen_but_old = []

    for event in all_events:
        h = make_hash(event)
        last_shown = seen.get(h)
        if last_shown is None:
            unseen.append(event)
        else:
            try:
                if (today - date.fromisoformat(last_shown)).days >= 7:
                    seen_but_old.append(event)
            except Exception:
                unseen.append(event)

    pool = unseen + seen_but_old

    if not pool:
        logger.info("All events seen recently — resetting seen registry for freshness.")
        clear_seen_registry()
        pool = all_events

    day_index = today.weekday()
    scored = sorted(pool, key=lambda e: score(e, day_index), reverse=True)

    # source cap: max 2 per source
    picked = []
    source_count = {}
    for event in scored:
        src = event.get("source", "?")
        if source_count.get(src, 0) < 2:
            picked.append(event)
            source_count[src] = source_count.get(src, 0) + 1
        if len(picked) == count:
            break

    # Mark picked as seen today
    for event in picked:
        seen[make_hash(event)] = today.isoformat()
    save_seen_registry(seen)

    return picked


def build_header() -> str:
    """Returns a rich daily alert header."""
    day = date.today().strftime("%A, %d %B %Y")
    return (
        f"🌟 *Daily Hyderabad Opportunities — {day}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Fresh picks just for you 👇"
    )
