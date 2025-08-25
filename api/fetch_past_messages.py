import os
import re
import asyncio
from decimal import Decimal, InvalidOperation
from telethon import TelegramClient
from urllib.parse import urlparse
from dotenv import load_dotenv
import asyncpg
import datetime

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

# Buffers for batch inserts
signal_buffer = []
market_buffer = []
BATCH_SIZE = 50
FLUSH_INTERVAL = 5  # seconds

# ------------------- Helpers -------------------
def extract_decimal(value):
    try:
        cleaned = re.sub(r"[^\d.]+", "", value)
        return Decimal(cleaned)
    except (InvalidOperation, AttributeError):
        return None

def extract_value(key, lines):
    for line in lines:
        if key.lower() in line.lower():
            parts = line.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip()
    return None

def process_message(message_text, message_date, sender_name=None):
    lines = [line.strip() for line in message_text.splitlines() if line.strip()]
    lower_lines = [line.lower() for line in lines]

    is_signal = (
        any(line.startswith('#') for line in lines) and
        any('entry' in line for line in lower_lines) and
        any('profit' in line for line in lower_lines) and
        any('loss' in line for line in lower_lines)
    )

    # Make datetime naive UTC for asyncpg
    timestamp = message_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    if is_signal:
        first_line = lines[0] if lines else ""
        pair = first_line.split()[0].strip('#') if first_line else "UNKNOWN"
        setup_type = ("LONG" if "long" in first_line.lower()
                      else "SHORT" if "short" in first_line.lower()
                      else "UNKNOWN")

        entry_raw = extract_value("Entry", lines)
        leverage_raw = extract_value("Leverage", lines)
        tp1_raw = extract_value("Target 1", lines) or extract_value("TP1", lines)
        tp2_raw = extract_value("Target 2", lines) or extract_value("TP2", lines)
        tp3_raw = extract_value("Target 3", lines) or extract_value("TP3", lines)
        tp4_raw = extract_value("Target 4", lines) or extract_value("TP4", lines)
        stop_loss_raw = extract_value("Stop Loss", lines) or extract_value("SL", lines)

        entry = extract_decimal(entry_raw)
        leverage = None
        if leverage_raw:
            try:
                leverage = int(re.sub(r"[^\d]", "", leverage_raw))
            except ValueError:
                leverage = None
        tp1 = extract_decimal(tp1_raw)
        tp2 = extract_decimal(tp2_raw)
        tp3 = extract_decimal(tp3_raw)
        tp4 = extract_decimal(tp4_raw)
        stop_loss = extract_decimal(stop_loss_raw)

        signal_buffer.append((
            pair, setup_type, entry, leverage,
            tp1, tp2, tp3, tp4, stop_loss, timestamp, message_text
        ))
        return "signal"
    else:
        market_buffer.append((
            sender_name or "Unknown", message_text, timestamp
        ))
        return "market"

# ------------------- Database -------------------
async def create_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signal_messages (
                id SERIAL PRIMARY KEY,
                pair VARCHAR(50),
                setup_type VARCHAR(10),
                entry DECIMAL(18,8),
                leverage INTEGER,
                tp1 DECIMAL(18,8),
                tp2 DECIMAL(18,8),
                tp3 DECIMAL(18,8),
                tp4 DECIMAL(18,8),
                stop_loss DECIMAL(18,8),
                timestamp TIMESTAMP,
                full_message TEXT UNIQUE
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS market_messages (
                id SERIAL PRIMARY KEY,
                sender VARCHAR(50),
                text TEXT UNIQUE,
                timestamp TIMESTAMP
            );
        """)
        print("✅ Tables checked/created.")

async def flush_buffers(pool):
    global signal_buffer, market_buffer
    async with pool.acquire() as conn:
        if signal_buffer:
            await conn.executemany("""
                INSERT INTO signal_messages
                (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                ON CONFLICT (full_message) DO NOTHING
            """, signal_buffer)
            signal_buffer = []

        if market_buffer:
            await conn.executemany("""
                INSERT INTO market_messages
                (sender, text, timestamp)
                VALUES ($1,$2,$3)
                ON CONFLICT (text) DO NOTHING
            """, market_buffer)
            market_buffer = []

# ------------------- Main -------------------
async def fetch_past_messages():
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    await create_tables(pool)

    async with TelegramClient("fetch_past_session", API_ID, API_HASH) as client:

        async def flush_periodically():
            while True:
                await asyncio.sleep(FLUSH_INTERVAL)
                await flush_buffers(pool)

        # Background flush task
        asyncio.create_task(flush_periodically())

        # Fetch past messages
        async for message in client.iter_messages(GROUP_ID, limit=100):
            if not message.message:
                continue

            sender_name = "Unknown"
            if message.sender_id:
                sender_entity = await client.get_entity(message.sender_id)
                sender_name = getattr(sender_entity, 'first_name', None) or getattr(sender_entity, 'username', 'Unknown')

            process_message(message.message.strip(), message.date, sender_name)

        # Final flush
        await flush_buffers(pool)
    await pool.close()

# ------------------- Run -------------------
if __name__ == "__main__":
    asyncio.run(fetch_past_messages())
