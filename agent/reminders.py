import logging
from datetime import datetime, timedelta

async def schedule_follow_up(context, event_title, chat_id):
    """Schedules a smart follow-up message 2 days later."""
    from .main import follow_up_job
    logging.info(f"Scheduling follow-up for {event_title} in chat {chat_id}")
    context.job_queue.run_once(
        follow_up_job, 
        when=timedelta(days=2), 
        data=event_title, 
        chat_id=chat_id
    )

async def check_reminders(context):
    """Checks for registration deadlines and sends 'Last Call' alerts."""
    logging.info("Checking for reminders...")
    # Mock logic: In real usage, this would query a database/scout
    pass
