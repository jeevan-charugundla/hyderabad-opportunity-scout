# 🚀 Hyderabad Opportunity Scout: Run Guide

Follow these steps to start your automated opportunity scout!

## 1. Prerequisites
- **Python 3.10+** installed.
- **Telegram Bot Token** (which you've already provided and I've added to `.env`).

## 2. Installation
Open your terminal in the `hyderabad-opportunity-scout` folder and run:
```bash
pip install -r requirements.txt
```

## 3. Configuration
Your settings are stored in `.env`. You can change these anytime:
- `DAILY_NOTIFY_TIME=19:00` (Change if you want alerts at a different time).
- `MAX_PRICE=150` (The strictly-under-150-INR filter).

## 4. Running the Agent
To start the bot and the daily scout:
```bash
python -m agent.main
```

## 5. How to use it
- **Daily Alerts**: You'll get messages at 7 PM IST every day.
- **Add to Calendar**: Click the button in the message (Ensure you've connected Google Calendar via Rube MCP).
- **Poster Scan**: Forward any event poster (image) to the bot, and it will scan the text for you!
- **Project Ideas**: If you add an event, wait 2 days for the bot to send you AI-generated project ideas.

---
**Happy Scouting!** 🚀
