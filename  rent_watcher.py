import os, re
from urllib.parse import quote
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION = os.getenv("TELEGRAM_SESSION", "")
CHANNELS = [c.strip() for c in os.getenv("CHANNELS", "").split(",") if c.strip()]
MAX_RENT_GEL = int(os.getenv("MAX_RENT_GEL", "0"))
AREAS = {a.strip().lower() for a in os.getenv("AREAS", "").split(",") if a.strip()}
STREETS = {s.strip().lower() for s in os.getenv("STREETS", "").split(",") if s.strip()}
FORWARD_TO = os.getenv("FORWARD_TO", "me").strip() or "me"
USD_TO_GEL = float(os.getenv("USD_TO_GEL", "0"))

if not API_ID or not API_HASH or not CHANNELS:
    raise SystemExit("Fill TELEGRAM_API_ID, TELEGRAM_API_HASH & CHANNELS in .env")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH) if SESSION else TelegramClient("rent_session", API_ID, API_HASH)

PRICE_RE = re.compile(r'(?<!\d)(\d[\d\s,\.]{1,})(?:\s*(₾|gel|lari|лари|\$|usd))?', re.IGNORECASE)

def parse_price_gel(text: str) -> int | None:
    m = PRICE_RE.search(text)
    if not m:
        return None
    amount_raw, unit = m.groups()
    digits = re.sub(r'[^\d]', '', amount_raw or "")
    if not digits:
        return None
    val = int(digits)
    if val < 50 or val > 200_000:
        return None
    unit = (unit or "gel").lower()
    if unit in ("$", "usd"):
        if USD_TO_GEL > 0:
            val = int(round(val * USD_TO_GEL))
        else:
            return None
    return val

def has_location_match(text: str) -> bool:
    low = text.lower()
    return (not AREAS and not STREETS) or any(a in low for a in AREAS) or any(s in low for s in STREETS)

def build_post_link(username: str, msg_id: int) -> str:
    return f"https://t.me/{quote(username.strip('@'))}/{msg_id}"

@client.on(events.NewMessage(chats=CHANNELS))
async def on_new_post(event):
    msg = event.message
    text = (msg.message or "").strip()
    if not text:
        return

    price_gel = parse_price_gel(text)
    price_ok = (MAX_RENT_GEL <= 0) or (price_gel is not None and price_gel <= MAX_RENT_GEL)
    loc_ok = has_location_match(text)

    if price_ok and loc_ok:
        link = ""
        try:
            entity = await event.get_chat()
            if getattr(entity, "username", None):
                link = build_post_link(entity.username, msg.id)
        except Exception:
            pass

        lines = ["✅ Найдена подходящая аренда"]
        if price_gel is not None:
            lines.append(f"Цена≈ {price_gel} GEL (порог {MAX_RENT_GEL} GEL)")
        if AREAS or STREETS:
            lines.append("Совпадение по локации")
        if link:
            lines.append(link)

        header = " | ".join(lines)
        await client.send_message(FORWARD_TO, header)
        await client.forward_messages(FORWARD_TO, msg)

if __name__ == "__main__":
    print("▶️ Rent watcher is running…")
    with client:
        client.run_until_disconnected()
