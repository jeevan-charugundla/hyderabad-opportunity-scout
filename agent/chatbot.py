import os
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from .scout import discover_events

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

def build_event_context():
    """Builds a text summary of all current events to feed to Gemini as context."""
    events = discover_events()
    if not events:
        return "No events available currently."
    
    lines = []
    for i, e in enumerate(events, 1):
        price_str = "FREE" if e['is_free'] else f"Rs.{e['price']}"
        cats = ", ".join(e.get('categories', []))
        lines.append(
            f"{i}. {e['title']}\n"
            f"   Categories: {cats}\n"
            f"   Register By: {e['deadline_display']}\n"
            f"   Event Date: {e['date']}\n"
            f"   Venue: {e['location']}\n"
            f"   Entry: {price_str}\n"
            f"   Source: {e.get('source', 'Web')}\n"
            f"   Link: {e['link']}\n"
        )
    return "\n".join(lines)


SYSTEM_PROMPT = """
You are OpportunityBot, a friendly and smart Telegram assistant for a college student in Hyderabad, India.
Your job is to help the user discover, choose, and prepare for hackathons, workshops, and tech meetups happening in Hyderabad.

Here are the CURRENT REAL EVENTS you know about (updated today):

{event_context}

Your personality:
- Friendly, encouraging, like a knowledgeable senior friend
- Keep responses short and punchy (max 3-4 lines per reply)
- Use relevant emojis naturally
- Always mention registration deadlines when relevant
- If someone asks about an event, give them the link directly
- If they ask "which one should I go to?", ask about their skills/interests first

If a user asks for "more events", "show me more", or "what else?", briefly describe 2-3 additional events from your list that haven't been highlighted recently. Always encourage them to use the 📢 "Give me update" button for the full card layout.

If the question is unrelated to tech events, gently redirect: "I'm your Hyderabad tech scout! Ask me about hackathons, workshops, or prep tips 🚀"
"""


async def chat_with_gemini(user_message: str) -> str:
    """Sends user message to Gemini with event context and returns the response."""
    try:
        event_context = build_event_context()
        prompt = SYSTEM_PROMPT.format(event_context=event_context)
        
        response = model.generate_content(
            [prompt, f"User says: {user_message}"]
        )
        return response.text.strip()
    
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        return (
            "🤖 I'm having a tiny brain glitch! Try again in a moment.\n"
            "Or click 📢 Give me update to see all events directly."
        )
