"""
bot.py — Telegram handlers for Hyderabad Opportunity Scout
All links/buttons are correctly built for robustness.
"""
import logging
import os
import json
from datetime import datetime
from urllib.parse import quote

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import ContextTypes

from .config import TELEGRAM_BOT_TOKEN
from .scout import discover_events, filter_events
from .chatbot import chat_with_gemini, scan_poster

logger = logging.getLogger(__name__)

STARRED_FILE = "starred_events.json"


# ─────────────────────────── LINK BUILDERS ──────────────────────────────────

def parse_date_safe(date_str: str):
    """Try multiple formats to parse a date string."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%B %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


def build_calendar_link(event: dict) -> str:
    """Build a Google Calendar link that always works."""
    name = quote(event.get("title", event.get("name", "Event")))
    venue_raw = event.get("location", event.get("venue", "Hyderabad"))
    venue = quote(f"{venue_raw}, Hyderabad")

    date_str = event.get("start_time", event.get("reg_deadline", event.get("date", "")))
    parsed = parse_date_safe(date_str) if date_str else None

    if parsed:
        d = parsed.strftime("%Y%m%d")
        dates_param = f"&dates={d}T090000/{d}T180000"
    else:
        dates_param = ""

    return (
        f"https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE&text={name}&location={venue}{dates_param}"
    )


def build_map_link(event: dict) -> str:
    """Build a Google Maps link that always works."""
    venue = event.get("location", event.get("venue", "Hyderabad"))
    query = quote(f"{venue}, Telangana, India")
    return f"https://www.google.com/maps/search/?api=1&query={query}"


def safe_register_link(event: dict) -> str:
    """Return the event link if valid, else fall back to Unstop search."""
    link = event.get("register_link", event.get("link", ""))
    if link and link.startswith("http"):
        return link
    name = quote(event.get("title", event.get("name", "")))
    return f"https://unstop.com/hackathons?search={name}"


# ─────────────────────────── CARD FORMATTER ─────────────────────────────────

def format_event_card(event: dict):
    """Build the message text and InlineKeyboardMarkup for an event card."""
    title = event.get("title", event.get("name", "Event"))
    date_val = event.get("deadline_display", event.get("date", "Date TBD"))
    venue = event.get("location", event.get("venue", "Hyderabad"))
    categories = " | ".join(event.get("categories", []))

    fee = int(event.get("price", event.get("fee", 0)) or 0)
    fee_display = "🆓 Free" if fee == 0 else f"💰 ₹{fee}"
    tag = "[🔥 FREE] " if fee == 0 else ""
    source = event.get("source", "Web")
    description = event.get("description", "")[:120]

    register_url = safe_register_link(event)
    calendar_url = build_calendar_link(event)
    map_url = build_map_link(event)

    text = (
        f"{tag}*{title}*\n"
        f"🏷️ _{categories}_\n\n"
        f"⏰ *Register By*: {date_val}\n"
        f"📍 *Venue*: {venue}\n"
        f"{fee_display}  •  🌐 {source}\n"
        f"🔗 [Register Here]({register_url})\n\n"
        f"_{description}_"
    )

    # Use short safe keys for callback data (max 64 bytes in Telegram)
    short_title = title[:30].replace("|", "-")
    short_date = (event.get("reg_deadline", event.get("date", ""))[:10])

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ I'm Going!", callback_data=f"going|{short_title}|{short_date}"),
            InlineKeyboardButton("🔖 Save", callback_data=f"save|{short_title}|{short_date}"),
        ],
        [
            InlineKeyboardButton("🗺 Venue Map", url=map_url),
            InlineKeyboardButton("📅 Add to Calendar", url=calendar_url),
        ],
    ])

    return text, keyboard


# ─────────────────────────── KEYBOARDS ──────────────────────────────────────

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("📢 Give me update")],
        [KeyboardButton("⭐ My Saved Events"), KeyboardButton("❓ Help")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_event_keyboard(event: dict) -> InlineKeyboardMarkup:
    """Backward-compatible wrapper used by other modules."""
    _, kb = format_event_card(event)
    return kb


# ─────────────────────────── SAVED EVENTS ───────────────────────────────────

def save_starred_event(event_data: dict):
    stars = []
    if os.path.exists(STARRED_FILE):
        try:
            with open(STARRED_FILE) as f:
                stars = json.load(f)
        except Exception:
            stars = []
    stars.append(event_data)
    with open(STARRED_FILE, "w") as f:
        json.dump(stars, f, indent=2)


def load_starred_events() -> list:
    if not os.path.exists(STARRED_FILE):
        return []
    try:
        with open(STARRED_FILE) as f:
            return json.load(f)
    except Exception:
        return []


# ─────────────────────────── COMMAND HANDLERS ───────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # Subscribe the user
    subs = context.bot_data.setdefault("subscribers", set())
    subs.add(chat_id)
    logger.info(f"User subscribed: {chat_id}")

    await update.message.reply_text(
        f"🚀 *Welcome to Hyderabad Opportunity Scout!*\n\n"
        "I'll alert you every day at *8 PM IST* with fresh hackathons, workshops and meetups.\n"
        "You can also click *📢 Give me update* anytime for instant results!\n\n"
        "📸 *Pro tip*: Send me a photo of any event poster and I'll extract the details instantly!",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(),
    )
    await sample(update, context)


async def sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends ALL active events as individual cards sorted by deadline."""
    events = discover_events()
    if not events:
        await update.message.reply_text("🔎 No upcoming events found right now. Check back later!")
        return

    await update.message.reply_text(
        f"🔍 *Found {len(events)} opportunities!* (sorted by deadline)\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown",
    )
    for event in events:
        text, keyboard = format_event_card(event)
        await update.message.reply_text(text=text, parse_mode="Markdown", reply_markup=keyboard)


# ─────────────────────────── MESSAGE HANDLER ────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📢 Give me update":
        await update.message.reply_text("⚡ *Fetching latest opportunities...*", parse_mode="Markdown")
        await sample(update, context)

    elif text == "⭐ My Saved Events":
        saved = load_starred_events()
        if not saved:
            await update.message.reply_text("You haven't saved any events yet. Use 🔖 Save on any card!")
        else:
            lines = [f"• {e.get('title', 'Event')}" for e in saved[-5:]]
            await update.message.reply_text(
                "⭐ *Your Saved Events (last 5)*:\n" + "\n".join(lines),
                parse_mode="Markdown",
            )

    elif text == "❓ Help":
        await update.message.reply_text(
            "ℹ️ *How to use Hyderabad Opportunity Scout*\n\n"
            "• 📢 *Give me update* — See all active events\n"
            "• 📸 *Send a poster image* — I'll scan and extract event details\n"
            "• ✅ *I'm Going!* — Save event + get AI project ideas in 48h\n"
            "• 🔖 *Save* — Bookmark an event quietly\n"
            "• /testalert — Test the 8 PM daily alert right now\n\n"
            "I send fresh events every evening at *8 PM IST* automatically! 🚀",
            parse_mode="Markdown",
        )

    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await chat_with_gemini(text)
        await update.message.reply_text(reply, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())


# ─────────────────────────── CALLBACK HANDLER ───────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    parts = query.data.split("|")
    action = parts[0]
    event_name = parts[1] if len(parts) > 1 else "Event"
    event_date = parts[2] if len(parts) > 2 else ""

    if action == "going":
        going = context.user_data.setdefault("going_events", [])
        going.append({"name": event_name, "date": event_date})

        # Schedule 48h follow-up with AI project ideas
        context.job_queue.run_once(
            _send_project_ideas_job,
            when=172800,  # 48 hours
            chat_id=query.message.chat_id,
            data={"event_name": event_name, "chat_id": query.message.chat_id},
            name=f"ideas_{query.message.chat_id}_{event_name[:10]}",
        )

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"🎉 Awesome! You're going to *{event_name}*!\n"
                "⏰ I'll send you 3 tailored project ideas in *48 hours*. Stay hyped! 🚀"
            ),
            parse_mode="Markdown",
        )

    elif action == "save":
        saved = context.user_data.setdefault("saved_events", [])
        saved.append({"name": event_name, "date": event_date})
        save_starred_event({"title": event_name, "date": event_date})
        await query.answer(f"🔖 Saved: {event_name[:30]}", show_alert=True)

    # legacy support
    elif action.startswith("going_"):
        from .reminders import schedule_follow_up
        title = action.split("_", 1)[1]
        await schedule_follow_up(context, title, query.message.chat_id)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ *Marked as going!* Follow-up scheduled for: *{title}*",
            parse_mode="Markdown",
        )

    elif action.startswith("save_"):
        title = action.split("_", 1)[1]
        save_starred_event({"title": title})
        await query.answer(text=f"⭐ Saved: {title[:30]}", show_alert=True)

    elif action.startswith("draft_"):
        title = action.split("_", 1)[1]
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"📝 *Application Draft for:*\n*{title}*\n\n"
                "\"I am a passionate technology enthusiast from Hyderabad with experience in building "
                "real-world projects. I want to participate to collaborate with fellow builders, "
                "learn from mentors, and showcase my technical skills in a competitive environment.\""
            ),
            parse_mode="Markdown",
        )


async def _send_project_ideas_job(context: ContextTypes.DEFAULT_TYPE):
    """48h later: send AI project ideas to the user."""
    from .chatbot import generate_project_ideas
    data = context.job.data
    event_name = data.get("event_name", "your event")
    chat_id = data.get("chat_id")
    ideas = await generate_project_ideas(event_name)
    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"👋 *Hey! Time to prep for {event_name}!*\n\n"
            f"Here are 3 unique project ideas just for you:\n\n{ideas}\n\n"
            "Good luck building! 🚀"
        ),
        parse_mode="Markdown",
    )


# ─────────────────────────── PHOTO HANDLER ──────────────────────────────────

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Downloads the photo and uses Gemini Vision to extract event details."""
    message = update.message
    if not message.photo:
        return

    photo_file = await message.photo[-1].get_file()
    temp_dir = "temp_scans"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"{photo_file.file_id}.jpg")

    try:
        await photo_file.download_to_drive(temp_path)
        status_msg = await update.message.reply_text("🧐 *Scanning Poster with AI...*", parse_mode="Markdown")
        details = await scan_poster(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not details:
        await status_msg.edit_text("❌ Sorry, I couldn't extract details. Make sure the poster is clear!")
        return

    summary = (
        f"✅ *Poster Scanned Successfully!*\n\n"
        f"📌 *Event*: {details.get('title', 'Unknown')}\n"
        f"📅 *Date*: {details.get('date', 'Unknown')}\n"
        f"📍 *Venue*: {details.get('location', 'Unknown')}\n"
        f"⏰ *Deadline*: {details.get('registration_deadline', 'Not mentioned')}\n\n"
        f"📝 *About*: {details.get('description', 'No description available.')}\n\n"
        "Would you like to add this to your calendar?"
    )

    # Enrich for get_event_keyboard compatibility
    enriched = {
        "title": details.get("title", "Scanned Event"),
        "name": details.get("title", "Scanned Event"),
        "location": details.get("location", "Hyderabad"),
        "venue": details.get("location", "Hyderabad"),
        "reg_deadline": details.get("registration_deadline") or "",
        "date": details.get("date") or "",
        "start_time": "",
        "link": details.get("link", "https://t.me/OpportunityScoutBot"),
        "register_link": details.get("link", "https://t.me/OpportunityScoutBot"),
        "price": 0,
        "fee": 0,
        "deadline_display": details.get("registration_deadline", details.get("date", "See poster")),
        "categories": ["Scanned Event"],
        "source": "Poster Scan",
        "description": details.get("description", ""),
        "is_free": True,
    }

    _, keyboard = format_event_card(enriched)

    await status_msg.delete()
    await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=keyboard)
