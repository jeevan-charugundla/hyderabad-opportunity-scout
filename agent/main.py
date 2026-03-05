import asyncio
import logging
import time
from datetime import datetime
import pytz
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from .config import TELEGRAM_BOT_TOKEN, DAILY_NOTIFY_TIME
from .bot import start, sample, button_handler, get_event_keyboard, handle_photo, handle_message
from .scout import discover_events, filter_events
from .reminders import check_reminders
from telegram.ext import MessageHandler, filters

async def send_daily_updates(application):
    logging.info("Starting daily update search...")
    # 1. Discover and Filter
    raw_events = discover_events()
    filtered_events = filter_events(raw_events)
    
    if not filtered_events:
        # In a real scenario, we might want to notify that no new events were found
        # but the user might prefer silence. We'll stick to the plan:
        # "No new low-cost opportunities found today"
        await application.bot.send_message(
            chat_id=application.bot_data.get('admin_chat_id'), 
            text="🔍 *Daily Update*: No new low-cost hackathons found in Hyderabad today."
        )
        return

    # 2. Send individual messages
    for event in filtered_events:
        tag = "[🔥 HIGH VALUE] " if event.get('is_free') else ""
        message = (
            f"{tag}*{event['title']}*\n\n"
            f"🚨 *REGISTRATION DEADLINE*: {event['reg_deadline']}\n"
            f"🗓️ *Event Date*: {event['date']}\n"
            f"📍 *Location*: {event['location']}\n"
            f"💰 *Entry*: ₹{event['price'] if event['price'] > 0 else '0 (FREE)'}\n\n"
            f"🔗 [Apply Here]({event['link']})"
        )
        
        await application.bot.send_message(
            chat_id=application.bot_data.get('admin_chat_id'),
            text=message,
            parse_mode='Markdown',
            reply_markup=get_event_keyboard(event)
        )

async def follow_up_job(context: ContextTypes.DEFAULT_TYPE):
    """Sends AI project ideas 2 days after calendar addition."""
    job = context.job
    follow_up_text = (
        f"👋 *Hey! Preparation time for {job.data}!* (AI Scout)\n\n"
        "Need a project idea? Here are 3 trending AI topics you could build:\n"
        "1️⃣ *Agentic RAG*: A bot that reads local docs and takes actions.\n"
        "2️⃣ *Multimodal Search*: Search your images using natural language.\n"
        "3️⃣ *Voice-to-Action*: Controlling apps using voice commands.\n\n"
        "Good luck building! 🚀"
    )
    await context.bot.send_message(chat_id=job.chat_id, text=follow_up_text, parse_mode='Markdown')

if __name__ == '__main__':
    import logging
    logging.info("Starting Hyderabad Opportunity Scout Agent...")
    
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('sample', sample))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Register Daily Jobs
    job_queue = application.job_queue
    # Daily search at 7 PM IST
    target_time = datetime.strptime(DAILY_NOTIFY_TIME, "%H:%M").time()
    job_queue.run_daily(lambda ctx: send_daily_updates(application), time=target_time)
    # Check for Last Call reminders every hour
    job_queue.run_repeating(check_reminders, interval=3600, first=10)
    
    # Start the bot
    print("Bot is running... Press Ctrl+C to stop.")
    application.run_polling()
