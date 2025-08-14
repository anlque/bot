from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os

api_id = int(os.getenv("TELEGRAM_API_ID") or input("API_ID: "))
api_hash = os.getenv("TELEGRAM_API_HASH") or input("API_HASH: ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("TELEGRAM_SESSION=", client.session.save())
