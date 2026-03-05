import logging
import time
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from urllib.parse import quote
from .config import TELEGRAM_BOT_TOKEN
from .scout import discover_events
from .chatbot import chat_with_gemini

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

STARRED_FILE = "starred_events.json"

def save_starred_event(event_data):
    stars = []
    if os.path.exists(STARRED_FILE):
        with open(STARRED_FILE, 'r') as f:
            stars = json.load(f)
    stars.append(event_data)
    with open(STARRED_FILE, 'w') as f:
        json.dump(stars, f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    logging.info(f"New interaction from Chat ID: {chat_id}")
    await update.message.reply_text(
        f"🚀 *Hyderabad Opportunity Scout Ready!*\n(Chat ID: `{chat_id}`)\n\n"
        "I'll send you updates every day at 8 PM, but you can click the button below anytime for an instant update!",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
    # Send the sample immediately
    await sample(update, context)

def get_main_menu_keyboard():
    """Returns a ReplyKeyboardMarkup for easy access to updates."""
    keyboard = [[KeyboardButton("📢 Give me update")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes messages: 'Give me update' shows all cards; anything else goes to Gemini AI."""
    text = update.message.text

    if text == "📢 Give me update":
        await update.message.reply_text("⚡ *Fetching latest opportunities...*", parse_mode='Markdown')
        await sample(update, context)
    else:
        # All other text → Gemini AI chatbot with live event context
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        reply = await chat_with_gemini(text)
        await update.message.reply_text(
            reply,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )

async def sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends ALL events filtered by deadline (closest first), one card each."""
    events = discover_events()
    if not events:
        await update.message.reply_text("🔎 No upcoming events found right now. Check back later!")
        return

    await update.message.reply_text(
        f"🔍 *Found {len(events)} opportunities for you!* (sorted by deadline)\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode='Markdown'
    )

    for event in events:
        tag = "[🔥 FREE] " if event.get('is_free') else ""
        categories = " | ".join(event.get('categories', []))
        message = (
            f"{tag}*{event['title']}*\n"
            f"🏷️ _{categories}_\n\n"
            f"⏰ *Register By*: {event['deadline_display']}\n"
            f"🗓️ *Event Date*: {event['date']}\n"
            f"📍 *Venue*: {event['location']}\n"
            f"💰 *Entry*: ₹{event['price'] if event['price'] > 0 else '0 (FREE)'}\n"
            f"🌐 *Source*: {event.get('source', 'Web')}\n\n"
            f"🔗 [Apply Here]({event['link']})"
        )
        await update.message.reply_text(
            text=message,
            parse_mode='Markdown',
            reply_markup=get_event_keyboard(event)
        )

def generate_calendar_url(event):
    """Generates a Google Calendar URL set to the REGISTRATION DEADLINE day.
    This is intentional — it reminds you to register BEFORE the deadline.
    """
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    title = quote(f"⏰ DEADLINE: Register for {event['title']}")
    # Use reg deadline for calendar (not event date) — so you get reminded to register!
    start = event['start_time'].replace("-", "").replace(":", "")
    end = event['end_time'].replace("-", "").replace(":", "")
    dates = f"{start}/{end}"
    detail_text = (
        f"📌 Register before: {event['deadline_display']}\n"
        f"📅 Event Date: {event['date']}\n"
        f"📍 Venue: {event['location']}\n"
        f"🔗 Apply: {event['link']}\n"
        f"🤖 Scouted by Hyderabad Opportunity Bot"
    )
    details = quote(detail_text)
    location = quote(event['location'])
    return f"{base_url}&text={title}&dates={dates}&details={details}&location={location}&sf=true&output=xml"

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("going_"):
        # Trigger Smart Follow-up
        from .reminders import schedule_follow_up
        event_title = data.split("_", 1)[1]
        await schedule_follow_up(context, event_title, query.message.chat_id)
        await query.answer(
            text=f"🚀 You're going to {event_title[:30]}! I'll check in with you in 2 days.",
            show_alert=True
        )
        # Send a confirmation as a NEW message (text messages have no caption to edit)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"✅ *Marked as going!* Follow-up scheduled for:\n*{event_title}*",
            parse_mode='Markdown'
        )
    elif data.startswith("save_"):
        event_title = data.split("_", 1)[1]
        save_starred_event({"id": data, "title": event_title})
        await query.answer(text=f"⭐ Saved: {event_title[:30]}", show_alert=True)
    elif data.startswith("draft_"):
        event_title = data.split("_", 1)[1]
        draft_text = (
            f"📝 *Application Draft for:*\n*{event_title}*\n\n"
            "\"“I am a passionate technology enthusiast from Hyderabad with experience in building "
            "real-world projects. I want to participate to collaborate with fellow builders, "
            "learn from mentors, and showcase my technical skills in a competitive environment.\""
        )
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=draft_text,
            parse_mode='Markdown'
        )

def get_event_keyboard(event):
    map_url = "https://www.google.com/maps/search/?api=1&query=" + quote(event['location'])
    cal_url = generate_calendar_url(event)
    # Truncate title to keep callback_data under 64 bytes (Telegram limit)
    short_title = event['title'][:40]
    
    keyboard = [
        [
            InlineKeyboardButton("📅 Add to Calendar", url=cal_url),
            InlineKeyboardButton("🗺️ Venue Map", url=map_url)
        ],
        [
            InlineKeyboardButton("🚀 I'm going!", callback_data=f"going_{short_title}"),
            InlineKeyboardButton("⭐ Save", callback_data=f"save_{short_title}")
        ],
        [
            InlineKeyboardButton("📝 Auto-Draft", callback_data=f"draft_{short_title}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Placeholder for OCR processing using AI or Tesseract."""
    await update.message.reply_text(
        "🧐 *Scanning Poster...*\n\n"
        "I've detected this might be a technical event! (OCR Simulation Enabled)\n"
        "Extracted: *Hyderabad Tech Meetup - March 30*\n"
        "Would you like me to add this to your calendar?",
        parse_mode='Markdown'
    )
