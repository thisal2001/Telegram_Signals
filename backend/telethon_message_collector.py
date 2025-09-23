import os
import re
import asyncio
import logging
from datetime import datetime, timezone

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.network import ConnectionTcpAbridged
from dotenv import load_dotenv
import asyncpg
import websockets
from websockets.exceptions import ConnectionClosed

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("app.log")]
)

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")
GROUP_ID = int(os.getenv("GROUP_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")
WS_HOST = "0.0.0.0"
WS_PORT = 8765

# ----------------------------
# Globals
# ----------------------------
signal_buffer = []
market_buffer = []
BATCH_SIZE = 10

# ----------------------------
# Helpers
# ----------------------------
def to_float_safe(val):
    try:
        return float(val) if val else None
    except Exception:
        return None

def parse_signal_message(text: str):
    """
    Detect and extract a trading signal.
    Returns tuple if valid signal, otherwise None.
    """

    text_clean = text.replace("\n", " ")

    # Pair detection (BTCUSDT, BTC/USDT, BTC-USDT, ETHUSDTPERP, etc.)
    pair_match = re.search(
        r"\b([A-Z]{2,10}(?:[-/ ]?USDT|USD|PERP))\b",
        text_clean,
        re.IGNORECASE
    )
    pair = (
        pair_match.group(1)
        .replace(" ", "")
        .replace("-", "")
        .replace("/", "")
        .upper()
        if pair_match
        else None
    )

    # LONG/SHORT
    setup_match = re.search(r"\b(LONG|SHORT)\b", text_clean, re.IGNORECASE)
    setup_type = setup_match.group(1).upper() if setup_match else None

    # Entry
    entry_match = re.search(r"(?:ENTRY|BUY|SELL)[:\s]*([\d\.]+)", text_clean, re.IGNORECASE)
    entry = entry_match.group(1) if entry_match else None

    # Leverage
    leverage_match = re.search(r"(\d+)\s*[xX]", text_clean)
    leverage = leverage_match.group(1) if leverage_match else None

    # Take Profits
    tp_matches = re.findall(r"TP\d*[:\s]*([\d\.]+)", text_clean, re.IGNORECASE)
    tp1, tp2, tp3, tp4 = (tp_matches + [None, None, None, None])[:4]

    # Stop Loss
    sl_match = re.search(r"(?:SL|STOP[-\s]?LOSS)[:\s]*([\d\.]+)", text_clean, re.IGNORECASE)
    stop_loss = sl_match.group(1) if sl_match else None

    # --- Decide if it's a signal ---
    if pair and setup_type and (entry or stop_loss or tp1):
        return (
            pair,
            setup_type,
            to_float_safe(entry),
            int(leverage) if leverage else None,
            to_float_safe(tp1),
            to_float_safe(tp2),
            to_float_safe(tp3),
            to_float_safe(tp4),
            to_float_safe(stop_loss),
        )
    else:
        return None

# ----------------------------
# Async Database Init
# ----------------------------
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            pair TEXT,
            setup_type TEXT,
            entry DECIMAL(18,8),
            leverage INT,
            tp1 DECIMAL(18,8),
            tp2 DECIMAL(18,8),
            tp3 DECIMAL(18,8),
            tp4 DECIMAL(18,8),
            stop_loss DECIMAL(18,8),
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            full_message TEXT
        );
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS market_messages (
            id SERIAL PRIMARY KEY,
            username TEXT,
            message TEXT,
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)
    await conn.close()
    logging.info("✅ PostgreSQL tables and indexes created")

# ----------------------------
# Batch Saver
# ----------------------------
async def save_batches():
    global signal_buffer, market_buffer
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        if signal_buffer:
            await conn.executemany("""
                INSERT INTO signals (
                    pair, setup_type, entry, leverage,
                    tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message
                ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            """, signal_buffer)
            logging.info(f"💾 Inserted {len(signal_buffer)} signals")
            signal_buffer = []

        if market_buffer:
            await conn.executemany("""
                INSERT INTO market_messages (
                    username, message, timestamp
                ) VALUES ($1,$2,$3)
            """, market_buffer)
            logging.info(f"💾 Inserted {len(market_buffer)} market messages")
            market_buffer = []

    except Exception as e:
        logging.error(f"❌ Batch insert failed: {e}")
    finally:
        await conn.close()

# ----------------------------
# Telegram Client
# ----------------------------
client = TelegramClient(
    StringSession(SESSION), API_ID, API_HASH,
    connection=ConnectionTcpAbridged
)

@client.on(events.NewMessage(chats=GROUP_ID))
async def handler(event):
    global signal_buffer, market_buffer
    sender = await event.get_sender()
    text = event.raw_text.strip()
    date = event.date.replace(tzinfo=timezone.utc)

    parsed = parse_signal_message(text)

    if parsed:
        logging.info(f"✅ Signal detected: {parsed[0]} {parsed[1]}")
        signal_buffer.append((
            parsed[0], parsed[1], parsed[2], parsed[3],
            parsed[4], parsed[5], parsed[6], parsed[7], parsed[8],
            date, text
        ))
    else:
        logging.info(f"📊 Market message: {text[:50]}...")
        market_buffer.append((
            sender.username or "unknown", text, date
        ))

    if len(signal_buffer) >= BATCH_SIZE or len(market_buffer) >= BATCH_SIZE:
        await save_batches()

# ----------------------------
# WebSocket Server
# ----------------------------
async def ws_handler(websocket):
    await websocket.send("✅ WebSocket connection established")
    while True:
        try:
            msg = await websocket.recv()
            logging.info(f"🌐 WS received: {msg}")
            await websocket.send(f"Echo: {msg}")
        except ConnectionClosed:
            logging.info("🔌 WebSocket disconnected")
            break

async def ws_server():
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        logging.info(f"🌐 WebSocket server running on ws://{WS_HOST}:{WS_PORT}")
        await asyncio.Future()  # run forever

# ----------------------------
# Main Entry
# ----------------------------
async def main():
    await init_db()
    await client.start()
    logging.info("✅ Telegram client started and authenticated")
    logging.info("👂 Listening for Telegram messages...")

    await asyncio.gather(
        client.run_until_disconnected(),
        ws_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
