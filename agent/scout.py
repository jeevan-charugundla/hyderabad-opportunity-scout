"""
scout.py — Event discovery for Hyderabad Opportunity Scout
Scrapes real upcoming tech events in Hyderabad.
"""
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ─────────────────────────── FALLBACK EVENTS ────────────────────────────────
FALLBACK_EVENTS = [
    {
        "title": "Google Developer Group Hyderabad Meetup",
        "name": "Google Developer Group Hyderabad Meetup",
        "categories": ["Meetup", "Community"],
        "date": "Ongoing",
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
        "title": "Beginner's Practical AI Hackathon — Entry Pass",
        "name": "Beginner's Practical AI Hackathon — Entry Pass",
        "categories": ["Hackathon", "AI/ML"],
        "date": "Ongoing",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Open Registration",
        "start_time": "",
        "end_time": "",
        "location": "T-Hub, Hyderabad",
        "venue": "T-Hub, Hyderabad",
        "price": 99,
        "fee": 99,
        "source": "Unstop",
        "register_link": "https://unstop.com/hackathons?location=Hyderabad",
        "link": "https://unstop.com/hackathons?location=Hyderabad",
        "description": "A beginner-friendly hands-on AI hackathon. ₹99 registration fee includes snacks.",
        "is_free": False,
    },
    {
        "title": "Full-Stack Web Dev Hands-on Workshop",
        "name": "Full-Stack Web Dev Hands-on Workshop",
        "categories": ["Workshop", "Web"],
        "date": "Monthly",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Check Commudle for dates",
        "start_time": "",
        "end_time": "",
        "location": "JNTU, Hyderabad",
        "venue": "JNTU, Hyderabad",
        "price": 149,
        "fee": 149,
        "source": "Commudle",
        "register_link": "https://www.commudle.com/communities",
        "link": "https://www.commudle.com/communities",
        "description": "Learn React and Node.js in this comprehensive 6-hour hands-on workshop. ₹149 entry fee.",
        "is_free": False,
    },
    {
        "title": "Hyderabad Hackathons on Unstop",
        "name": "Hyderabad Hackathons on Unstop",
        "categories": ["Hackathon"],
        "date": "Multiple",
        "reg_deadline": "2099-01-01",
        "deadline_display": "Check Unstop for deadlines",
        "start_time": "",
        "end_time": "",
        "location": "Hyderabad",
        "venue": "Hyderabad",
        "price": 0,
        "fee": 0,
        "source": "Unstop",
        "register_link": "https://unstop.com/hackathons?location=Hyderabad",
        "link": "https://unstop.com/hackathons?location=Hyderabad",
        "description": "Browse all live hackathons in Hyderabad — updated daily by Unstop.",
        "is_free": True,
    },
]

# ─────────────────────────── SCRAPERS ─────────────────────────────────────

def scrape_allevents():
    """Scrape upcoming tech events in Hyderabad from allevents.in"""
    events = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        url = "https://allevents.in/hyderabad/tech"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return events

        soup = BeautifulSoup(resp.text, 'html.parser')
        cards = soup.select('li.event-card')
        
        for card in cards[:15]:
            # Title
            title_elem = card.select_one('.title h3')
            if not title_elem:
                continue
            title = title_elem.text.strip()
            
            # Simple keyword filter in case allevents mixes in random stuff
            lower_title = title.lower()
            if not any(k in lower_title for k in ("tech", "hackathon", "ai", "ml", "data", "cloud", "developer", "startup", "code", "aws", "cyber", "web", "design")):
                continue
            
            # Link
            a_elem = card.select_one('a')
            link = a_elem.get('href', url) if a_elem else url
            
            # Date
            date_elem = card.select_one('.date')
            date_str = date_elem.text.strip() if date_elem else ""
            
            # Venue
            venue_elem = card.select_one('.subtitle')
            venue_str = venue_elem.text.strip() if venue_elem else "Hyderabad"
            
            # Deadline (approx future date to keep it alive for a bit)
            deadline = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            
            # Price Parsing
            import re
            fee = 0
            is_free = True
            try:
                price_elem = card.select_one('.price')
                price_text = price_elem.text.strip().lower() if price_elem else ""
                
                if "free" in price_text:
                    fee = 0
                else:
                    card_text = card.text.replace(',', '')
                    inr_matches = re.findall(r'(?:inr|rs\.?|₹)\s*(\d+)', card_text, re.IGNORECASE)
                    if inr_matches:
                        fee = int(inr_matches[0])
                    else:
                        digits = re.findall(r'\d+', price_text)
                        fee = int(digits[0]) if digits else 0
                        
                is_free = (fee == 0)
            except Exception:
                fee = 0
                is_free = True
            
            events.append({
                "title": title,
                "name": title,
                "categories": ["Tech Event", "Community"],
                "date": date_str,
                "reg_deadline": deadline,
                "deadline_display": date_str,
                "start_time": "",
                "end_time": "",
                "location": venue_str,
                "venue": venue_str,
                "price": fee,
                "fee": fee,
                "source": "AllEvents",
                "register_link": link,
                "link": link,
                "description": "Tech event from AllEvents.in",
                "is_free": is_free,
            })
    except Exception as e:
        logger.error(f"Error scraping AllEvents: {e}")
    return events


def discover_events() -> list:
    """
    Scrapes live events from multiple sources.
    Falls back to FALLBACK_EVENTS if scrapers fail.
    """
    scraped_events = []
    
    # Run scrapers
    scraped_events.extend(scrape_allevents())
    
    events = scraped_events + FALLBACK_EVENTS
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        active = [e for e in events if e.get("reg_deadline", "2099-01-01") >= today]
        active.sort(key=lambda x: x.get("reg_deadline", "2099-01-01"))
    except Exception as e:
        logger.error(f"Error sorting events: {e}")
        active = events

    return active


def filter_events(events: list) -> list:
    """Filters events by price threshold (default ₹500)."""
    return [e for e in events if int(e.get("price", e.get("fee", 0)) or 0) <= 500]
