import os
import re
import psycopg2
from decimal import Decimal, InvalidOperation
from telethon import TelegramClient
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    url = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return conn

def create_tables():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
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
        print("✅ Checked/Created: signal_messages table")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_messages (
                id SERIAL PRIMARY KEY,
                sender VARCHAR(50),
                text TEXT UNIQUE,
                timestamp TIMESTAMP
            );
        """)
        print("✅ Checked/Created: market_messages table")

        conn.commit()
    conn.close()

def extract_decimal(value):
    try:
        # Remove any non-digit/dot characters like commas, spaces, etc.
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

def save_signal(conn, pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message):
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM signal_messages WHERE full_message = %s", (full_message,))
        if cursor.fetchone():
            print("Duplicate signal message skipped.")
            return
        cursor.execute("""
            INSERT INTO signal_messages
            (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message))
        conn.commit()
        print(f"Saved signal message: {pair} {setup_type} at {timestamp}")

def save_market(conn, sender, text, timestamp):
    with conn.cursor() as cursor:
        cursor.execute("SELECT 1 FROM market_messages WHERE text = %s", (text,))
        if cursor.fetchone():
            print("Duplicate market message skipped.")
            return
        cursor.execute("""
            INSERT INTO market_messages (sender, text, timestamp)
            VALUES (%s, %s, %s)
        """, (sender, text, timestamp))
        conn.commit()
        print(f"Saved market message from {sender} at {timestamp}")

async def fetch_past_messages():
    create_tables()
    conn = get_db_connection()
    async with TelegramClient("fetch_past_session", API_ID, API_HASH) as client:
        async for message in client.iter_messages(GROUP_ID, limit=100):
            if not message.message:
                continue

            text = message.message.strip()
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            lower_lines = [line.lower() for line in lines]

            # Simple signal detection heuristic
            is_signal = (
                any(line.startswith('#') for line in lines) and
                any('entry' in line for line in lower_lines) and
                any('profit' in line for line in lower_lines) and
                any('loss' in line for line in lower_lines)
            )

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

                save_signal(conn, pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, message.date, text)

            else:
                sender = "Unknown"
                if message.sender_id:
                    sender_entity = await client.get_entity(message.sender_id)
                    sender = getattr(sender_entity, 'first_name', None) or getattr(sender_entity, 'username', 'Unknown')

                save_market(conn, sender, text, message.date)

    conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(fetch_past_messages())
