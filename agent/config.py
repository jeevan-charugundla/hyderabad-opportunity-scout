import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SEARCH_LOCATION = os.getenv("SEARCH_LOCATION", "Hyderabad")
MAX_PRICE = int(os.getenv("MAX_PRICE", 150))
DAILY_NOTIFY_TIME = os.getenv("DAILY_NOTIFY_TIME", "19:00")
