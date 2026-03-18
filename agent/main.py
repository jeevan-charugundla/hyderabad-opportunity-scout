"""
main.py — Entry point for Hyderabad Opportunity Scout
Runs the Telegram bot with reliable 8 PM IST daily alerts.
"""
import asyncio
import logging
from datetime import time as dt_time

from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import TELEGRAM_BOT_TOKEN
from .bot import (
    start,
    sample,
    button_handler,
    get_event_keyboard,
    handle_photo,
    handle_message,
)
from .scout import discover_events, filter_events
from .alert_engine import get_fresh_events, build_header
from .bot import format_event_card

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


# ─────────────────────────── CORE ALERT LOGIC ────────────────────────────────

async def _run_alert(bot, user_ids: list):
    """Core alert logic — fetches fresh events and sends them to all subscribers."""
    all_events = discover_events()
    picks = get_fresh_events(all_events, count=5)
    header = build_header()

    for uid in user_ids:
        try:
            await bot.send_message(chat_id=uid, text=header, parse_mode="Markdown")
            for event in picks:
                text, keyboard = format_event_card(event)
                await bot.send_message(chat_id=uid, text=text, parse_mode="Markdown", reply_markup=keyboard)
            await bot.send_message(
                chat_id=uid,
                text=(
                    "━━━━━━━━━━━━━━━━━\n"
                    "📌 Tap *I'm Going!* → get AI project ideas in 48h\n"
                    "🔖 *Save* → bookmark it quietly\n"
                    "📢 *Give me update* → see all events anytime"
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Failed to send alert to {uid}: {e}")


async def send_daily_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled daily alert — fires at 8 PM IST to all subscribers."""
    subscribers = context.bot_data.get("subscribers", set())
    if not subscribers:
        logger.info("No subscribers yet — skipping daily alert.")
        return
    logger.info(f"Sending daily alerts to {len(subscribers)} subscribers...")
    await _run_alert(context.bot, list(subscribers))


# ─────────────────────────── FOLLOW-UP JOB ───────────────────────────────────

async def follow_up_job(context: ContextTypes.DEFAULT_TYPE):
    """Sends AI project ideas 48 hours after a user marks I'm Going."""
    from .chatbot import generate_project_ideas
    job = context.job
    event_title = job.data
    ideas = await generate_project_ideas(event_title)
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=(
            f"👋 *Hey! Preparation time for {event_title}!* (AI Scout)\n\n"
            f"Looking for something to build? Here are 3 unique project ideas:\n\n"
            f"{ideas}\n\n"
            "Good luck building! 🚀"
        ),
        parse_mode="Markdown",
    )


# ─────────────────────────── TEST ALERT COMMAND ──────────────────────────────

async def test_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/testalert — instantly triggers the 8 PM alert logic for the current user."""
    uid = update.effective_user.id
    await update.message.reply_text("🧪 Triggering test alert now... you'll get your daily picks! 📬")
    await _run_alert(context.bot, [uid])


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/events — alias for the main update button."""
    await update.message.reply_text("⚡ *Fetching latest opportunities...*", parse_mode="Markdown")
    await sample(update, context)


# ─────────────────────────── MAIN ────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("Starting Hyderabad Opportunity Scout Agent...")

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # ── Handlers ──────────────────────────────────────────────────────────────
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sample", sample))
    application.add_handler(CommandHandler("events", events_command))
    application.add_handler(CommandHandler("testalert", test_alert))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # ── Scheduled Jobs ────────────────────────────────────────────────────────
    job_queue = application.job_queue

    # Remove any stale duplicate jobs first
    for old_job in job_queue.get_jobs_by_name("daily_8pm_alert"):
        old_job.schedule_removal()

    # Register 8 PM IST daily job
    job_queue.run_daily(
        callback=send_daily_alerts,
        time=dt_time(hour=20, minute=0, second=0, tzinfo=IST),
        name="daily_8pm_alert",
    )

    logger.info("Bot is running. Daily alert scheduled for 20:00 IST.")
    print("✅ Bot is live. Press Ctrl+C to stop.")
    application.run_polling()
