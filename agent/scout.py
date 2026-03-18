"""
scout.py — Event discovery for Hyderabad Opportunity Scout
Static curated events + fallback events if scraping is unavailable.
Events auto-filtered by registration deadline.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ─────────────────────────── FALLBACK EVENTS ────────────────────────────────
# Always shown if all scrapers return empty — bot never goes silent.
FALLBACK_EVENTS = [
    {
        "title": "HackHyderabad 2025",
        "name": "HackHyderabad 2025",
        "categories": ["Hackathon"],
        "date": "",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Open Registration",
        "start_time": "",
        "end_time": "",
        "location": "T-Hub, Hyderabad",
        "venue": "T-Hub, Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Unstop",
        "register_link": "https://unstop.com/hackathons?location=Hyderabad",
        "link": "https://unstop.com/hackathons?location=Hyderabad",
        "description": "Annual student hackathon at T-Hub. Build, pitch, win.",
        "is_free": True,
    },
    {
        "title": "Google Developer Group Hyderabad Meetup",
        "name": "Google Developer Group Hyderabad Meetup",
        "categories": ["Meetup", "Community"],
        "date": "",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Open Registration",
        "start_time": "",
        "end_time": "",
        "location": "Gachibowli, Hyderabad",
        "venue": "Gachibowli, Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Meetup",
        "register_link": "https://gdg.community.dev/gdg-hyderabad/",
        "link": "https://gdg.community.dev/gdg-hyderabad/",
        "description": "Monthly tech meetup by GDG Hyderabad. Talks, networking, free snacks.",
        "is_free": True,
    },
    {
        "title": "Web3 & Blockchain Workshop",
        "name": "Web3 & Blockchain Workshop",
        "categories": ["Workshop", "Web3"],
        "date": "",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Open Registration",
        "start_time": "",
        "end_time": "",
        "location": "JNTU Hyderabad",
        "venue": "JNTU Hyderabad",
        "price": 100,
        "fee": 100,
        "source": "Commudle",
        "register_link": "https://www.commudle.com/communities",
        "link": "https://www.commudle.com/communities",
        "description": "Hands-on workshop on Solidity, smart contracts, and DeFi basics.",
        "is_free": False,
    },
    {
        "title": "AI/ML Bootcamp — Beginners",
        "name": "AI/ML Bootcamp — Beginners",
        "categories": ["Workshop", "AI/ML"],
        "date": "",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Open Registration",
        "start_time": "",
        "end_time": "",
        "location": "IIIT Hyderabad",
        "venue": "IIIT Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Unstop",
        "register_link": "https://unstop.com/workshops?location=Hyderabad",
        "link": "https://unstop.com/workshops?location=Hyderabad",
        "description": "Free 1-day bootcamp covering Python, sklearn, and model deployment.",
        "is_free": True,
    },
    {
        "title": "Open Source Contributor Day",
        "name": "Open Source Contributor Day",
        "categories": ["Meetup", "Open Source"],
        "date": "",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Open Registration",
        "start_time": "",
        "end_time": "",
        "location": "Koramangala Community Space, Hyderabad",
        "venue": "Koramangala Community Space, Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Meetup",
        "register_link": "https://www.meetup.com/hyderabad-foss/",
        "link": "https://www.meetup.com/hyderabad-foss/",
        "description": "Beginner-friendly open source contribution sprint with mentors.",
        "is_free": True,
    },
]

# ─────────────────────────── CURATED EVENTS ─────────────────────────────────

CURATED_EVENTS = [
    {
        "title": "Yantra Yugam — 24Hr National Level Hackathon",
        "name": "Yantra Yugam — 24Hr National Level Hackathon",
        "categories": ["Hackathon", "National-Level", "ECE/IoT/CS"],
        "date": "March 24-25, 2026",
        "reg_deadline": "2026-03-22",
        "deadline_display": "March 22, 2026",
        "start_time": "2026-03-24T09:00:00",
        "end_time": "2026-03-25T18:00:00",
        "location": "Malla Reddy University, Hyderabad",
        "venue": "Malla Reddy University, Hyderabad",
        "price": 350,
        "fee": 350,
        "source": "Unstop",
        "register_link": "https://www.mallareddyuniversity.ac.in",
        "link": "https://www.mallareddyuniversity.ac.in",
        "description": "₹50,000 prize pool. Theme: Open Innovation. Web Dev, Drones, AIML, IoT, VLSI domains.",
        "is_free": False,
    },
    {
        "title": "VNR Design-A-Thon 2026",
        "name": "VNR Design-A-Thon 2026",
        "categories": ["Hackathon", "Design", "Product"],
        "date": "March 24-25, 2026",
        "reg_deadline": "2026-03-22",
        "deadline_display": "March 22, 2026",
        "start_time": "2026-03-22T09:00:00",
        "end_time": "2026-03-22T23:59:00",
        "location": "VNR VJIET, Bachupally, Hyderabad",
        "venue": "VNR VJIET, Bachupally, Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Unstop",
        "register_link": "https://unstop.com/o/1648514",
        "link": "https://unstop.com/o/1648514",
        "description": "Free design and product hackathon at VNR VJIET.",
        "is_free": True,
    },
    {
        "title": "GitTogether Hyderabad — March 2026 Meetup",
        "name": "GitTogether Hyderabad — March 2026 Meetup",
        "categories": ["Meetup", "Open Source", "Community"],
        "date": "March 21, 2026",
        "reg_deadline": "2026-03-20",
        "deadline_display": "March 20, 2026 (waitlist — register early!)",
        "start_time": "2026-03-21T10:00:00",
        "end_time": "2026-03-21T17:00:00",
        "location": "Venue TBD, Hyderabad",
        "venue": "Venue TBD, Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Meetup",
        "register_link": "https://www.meetup.com/gittogether-hyderabad/",
        "link": "https://www.meetup.com/gittogether-hyderabad/",
        "description": "Monthly GitHub community meetup — open source talks and contributions.",
        "is_free": True,
    },
    {
        "title": "Vivitsu 2026 — GRIET 24Hr Hackathon",
        "name": "Vivitsu 2026 — GRIET 24Hr Hackathon",
        "categories": ["Hackathon", "Engineering", "College"],
        "date": "March 31, 2026",
        "reg_deadline": "2026-03-28",
        "deadline_display": "March 28, 2026",
        "start_time": "2026-03-31T09:00:00",
        "end_time": "2026-04-01T09:00:00",
        "location": "GRIET, Bachupally, Hyderabad",
        "venue": "GRIET, Bachupally, Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "PlacementPrep",
        "register_link": "https://placementpreparation.io/hackathon/vivitsu-2026-griet/",
        "link": "https://placementpreparation.io/hackathon/vivitsu-2026-griet/",
        "description": "GRIET's flagship 24-hour hackathon — build anything, win prizes.",
        "is_free": True,
    },
    {
        "title": "FebAIThon — Global AI Hackathon (Hyderabad)",
        "name": "FebAIThon — Global AI Hackathon (Hyderabad)",
        "categories": ["Hackathon", "AI/ML", "Microsoft Fabric"],
        "date": "April 18, 2026",
        "reg_deadline": "2026-04-10",
        "deadline_display": "April 10, 2026",
        "start_time": "2026-04-18T09:00:00",
        "end_time": "2026-04-18T18:00:00",
        "location": "Microsoft Office, Gachibowli, Hyderabad",
        "venue": "Microsoft Office, Gachibowli, Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Meetup",
        "register_link": "https://www.meetup.com/hdac-community/",
        "link": "https://www.meetup.com/hdac-community/",
        "description": "Global AI hackathon with Microsoft Fabric, Azure, and ML track prizes.",
        "is_free": True,
    },
]


# ─────────────────────────── PUBLIC API ─────────────────────────────────────

def discover_events() -> list:
    """
    Returns all active curated events sorted by registration deadline.
    Falls back to FALLBACK_EVENTS if none are found.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        active = [e for e in CURATED_EVENTS if e.get("reg_deadline", "9999") >= today]
        active.sort(key=lambda x: x.get("reg_deadline", "9999"))
    except Exception as e:
        logger.error(f"Error filtering events: {e}")
        active = []

    if not active:
        logger.warning("No active curated events — using fallback events.")
        return FALLBACK_EVENTS

    return active


def filter_events(events: list) -> list:
    """Filters events by price threshold (default ₹500)."""
    return [e for e in events if int(e.get("price", e.get("fee", 0)) or 0) <= 500]
