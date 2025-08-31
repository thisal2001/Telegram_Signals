import os
import asyncio
import json
import asyncpg
from telethon import TelegramClient, events
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load env
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))
DB_URL = os.getenv("DATABASE_URL")

# Parse DB URL for Neon
def get_db_config():
    url = urlparse(DB_URL)
    return {
        'user': url.username,
        'password': url.password,
        'database': url.path[1:],
        'host': url.hostname,
        'port': url.port,
        'ssl': 'require'
    }

# DB pool
db_pool = None

# Buffers for batch inserts
signal_buffer = []
market_buffer = []
BATCH_SIZE = 10
FLUSH_INTERVAL = 5

def to_float_safe(value):
    if not value or value == "None" or value.lower() == "none":
        return None
    try:
        cleaned = ''.join(c for c in str(value) if c.isdigit() or c in ('.', '-'))
        if not cleaned or cleaned == '-':
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None

async def create_tables():
    async with db_pool.acquire() as conn:
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
        # Create indexes for better performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_timestamp ON signal_messages(timestamp);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_messages(timestamp);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_pair ON signal_messages(pair);")
        print("✅ PostgreSQL tables and indexes created")

async def flush_buffers():
    global signal_buffer, market_buffer
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)
        if not signal_buffer and not market_buffer:
            continue

        try:
            async with db_pool.acquire() as conn:
                if signal_buffer:
                    await conn.executemany("""
                        INSERT INTO signal_messages
                        (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                        ON CONFLICT (full_message) DO NOTHING
                    """, signal_buffer)
                    print(f"✅ Flushed {len(signal_buffer)} signals to PostgreSQL")

                if market_buffer:
                    await conn.executemany("""
                        INSERT INTO market_messages (sender, text, timestamp)
                        VALUES ($1,$2,$3)
                        ON CONFLICT (text) DO NOTHING
                    """, market_buffer)
                    print(f"✅ Flushed {len(market_buffer)} market messages to PostgreSQL")

                # Clear buffers after successful insert
                signal_buffer = []
                market_buffer = []

        except Exception as e:
            print(f"❌ Batch insert failed: {e}")
            import traceback
            traceback.print_exc()

def extract_value(label, lines):
    for line in lines:
        if label.lower() in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                value = parts[1].strip().replace("•", "").strip()
                if "stop loss" in label.lower() or "sl" in label.lower():
                    value = value.split('☠️')[0].strip()
                return value
    return None

async def run_telegram_client():
    # Use your existing session file instead of MemorySession
    client = TelegramClient('session', API_ID, API_HASH)

    await client.start()
    print("✅ Telegram client started and authenticated")

    @client.on(events.NewMessage(chats=GROUP_ID))
    async def handler(event):
        try:
            text = event.message.message
            date = event.message.date
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            is_signal = (
                any(line.startswith('#') for line in lines) and
                any('entry' in line.lower() for line in lines) and
                any('profit' in line.lower() for line in lines) and
                any('loss' in line.lower() for line in lines)
            )

            if is_signal:
                first_line = lines[0] if lines else ""
                pair = first_line.split()[0].strip('#') if first_line else "UNKNOWN"
                setup_type = ("LONG" if "LONG" in first_line.upper()
                              else "SHORT" if "SHORT" in first_line.upper()
                              else "UNKNOWN")

                entry = extract_value("Entry", lines)
                leverage = extract_value("Leverage", lines)
                tp1 = extract_value("Target 1", lines) or extract_value("TP1", lines)
                tp2 = extract_value("Target 2", lines) or extract_value("TP2", lines)
                tp3 = extract_value("Target 3", lines) or extract_value("TP3", lines)
                tp4 = extract_value("Target 4", lines) or extract_value("TP4", lines)
                stop_loss = extract_value("Stop Loss", lines) or extract_value("SL", lines)

                signal_buffer.append((
                    pair, setup_type,
                    to_float_safe(entry),
                    int(to_float_safe(leverage.replace('x',''))) if leverage and leverage != "None" else None,
                    to_float_safe(tp1), to_float_safe(tp2),
                    to_float_safe(tp3), to_float_safe(tp4),
                    to_float_safe(stop_loss), date, text
                ))

                print(f"✅ Signal detected: {pair} {setup_type}")

            else:
                sender = event.message.sender.first_name if event.message.sender else "Unknown"
                market_buffer.append((sender, text, date))
                print(f"📊 Market message: {text[:100]}...")

        except Exception as e:
            print(f"❌ Error processing message: {e}")
            import traceback
            traceback.print_exc()

    print("👂 Listening for Telegram messages...")
    await client.run_until_disconnected()

async def main():
    global db_pool

    try:
        # Database setup
        if not DB_URL:
            print("❌ DATABASE_URL environment variable is required")
            return

        db_config = get_db_config()
        db_pool = await asyncpg.create_pool(**db_config, min_size=1, max_size=10)
        print("✅ Connected to Neon PostgreSQL")

        # Create tables
        await create_tables()

        # Start buffer flusher
        asyncio.create_task(flush_buffers())

        # Start Telegram client
        await run_telegram_client()

    except Exception as e:
        print(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db_pool:
            await db_pool.close()
        print("🛑 Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())