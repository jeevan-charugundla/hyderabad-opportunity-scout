import asyncio
import os
from PIL import Image
from agent.chatbot import scan_poster

# Download a sample poster image
import requests
url = "https://s3.amazonaws.com/assets.mlh.io/events/splashes/000/212/575/thumb/MLH-Hack-Poster-1.png"
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
with open('test_poster.png', 'wb') as f:
    f.write(response.content)

async def main():
    print("Testing scan_poster...")
    details = await scan_poster("test_poster.png")
    print(details)

asyncio.run(main())
