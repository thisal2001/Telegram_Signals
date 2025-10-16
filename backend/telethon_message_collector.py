import os
import asyncio
import json
import asyncpg
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
from urllib.parse import urlparse
import websockets
from decimal import Decimal

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
GROUP_ID = int(os.getenv("GROUP_ID"))
DB_URL = os.getenv("DATABASE_URL")

# ----------------------------
# DB helper
# ----------------------------
def get_db_config():
    url = urlparse(DB_URL)
    return {
        "user": url.username,
        "password": url.password,
        "database": url.path[1:],
        "host": url.hostname,
        "port": url.port or 5432,
        "ssl": "require"
    }

async def get_connection():
    db_config = get_db_config()
    return await asyncpg.connect(**db_config)

# ----------------------------
# Globals
# ----------------------------
signal_buffer = []
market_buffer = []
buffer_lock = asyncio.Lock()  # ✅ protect buffers
BATCH_SIZE = 10
FLUSH_INTERVAL = 5
connected_clients = set()

# ----------------------------
# Utility
# ----------------------------
def to_decimal_safe(value):
    """Convert cleaned string to Decimal(18,8) or None"""
    if not value or str(value).lower() == "none":
        return None
    try:
        cleaned = ''.join(c for c in str(value) if c.isdigit() or c in ('.', '-'))
        if not cleaned or cleaned == "-":
            return None
        return Decimal(cleaned).quantize(Decimal("0.00000001"))
    except:
        return None

# ----------------------------
# DB tables
# ----------------------------
async def create_tables():
    conn = await get_connection()
    try:
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
                full_message TEXT UNIQUE,
                channel VARCHAR(100)
            );
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS market_messages (
                id SERIAL PRIMARY KEY,
                sender VARCHAR(100),
                text TEXT UNIQUE,
                timestamp TIMESTAMP
            );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_timestamp ON signal_messages(timestamp);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_messages(timestamp);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_pair ON signal_messages(pair);")
        print("✅ PostgreSQL tables and indexes created")
    finally:
        await conn.close()

# ----------------------------
# Batch insert to DB
# ----------------------------
async def flush_buffers():
    global signal_buffer, market_buffer
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)
        async with buffer_lock:
            if not signal_buffer and not market_buffer:
                continue
            try:
                conn = await get_connection()
                try:
                    if signal_buffer:
                        for row in signal_buffer:
                            await conn.execute("""
                                INSERT INTO signal_messages
                                (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message, channel)
                                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                                ON CONFLICT (full_message) DO NOTHING
                            """, *row)
                        print(f"✅ Flushed {len(signal_buffer)} signals to PostgreSQL")

                    if market_buffer:
                        for row in market_buffer:
                            await conn.execute("""
                                INSERT INTO market_messages (sender, text, timestamp)
                                VALUES ($1,$2,$3)
                                ON CONFLICT (text) DO NOTHING
                            """, *row)
                        print(f"✅ Flushed {len(market_buffer)} market messages to PostgreSQL")
                finally:
                    await conn.close()

                signal_buffer = []
                market_buffer = []
            except Exception as e:
                print(f"❌ Batch insert failed: {e}")

# ----------------------------
# WebSocket
# ----------------------------
async def websocket_handler(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            await websocket.send("Server received: " + message)
    except:
        pass
    finally:
        connected_clients.remove(websocket)

async def broadcast_message(message: str):
    if connected_clients:
        await asyncio.wait([client.send(message) for client in connected_clients])

async def start_websocket_server():
    server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    print("🌐 WebSocket server running on ws://0.0.0.0:8765")
    await server.wait_closed()

# ----------------------------
# Telegram message parser
# ----------------------------
def extract_value(label, lines):
    for line in lines:
        if label.lower() in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                value = parts[1].strip().replace("•", "").strip()
                if "stop loss" in label.lower() or "sl" in label.lower():
                    value = value.split('☠')[0].strip()
                return value
    return None

async def run_telegram_client():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    print("✅ Telegram client started and authenticated")

    @client.on(events.NewMessage(chats=GROUP_ID))
    async def handler(event):
        global signal_buffer, market_buffer
        try:
            text = event.message.message
            date = event.message.date
            if date.tzinfo is not None:
                date = date.replace(tzinfo=None)
            lines = [line.strip() for line in text.splitlines() if line.strip()]

            # Detect if it's a signal message
            is_signal = (
                any(line.startswith('#') for line in lines) and
                any('entry' in line.lower() for line in lines) and
                any('profit' in line.lower() for line in lines) and
                any('loss' in line.lower() for line in lines)
            )

            channel_name = event.chat.title or str(event.chat_id)

            async with buffer_lock:
                if is_signal:
                    first_line = lines[0] if lines else ""
                    pair = first_line.split()[0].strip('#') if first_line else "UNKNOWN"
                    setup_type = (
                        "LONG" if "LONG" in first_line.upper()
                        else "SHORT" if "SHORT" in first_line.upper()
                        else "UNKNOWN"
                    )

                    entry = extract_value("Entry", lines)
                    leverage = extract_value("Leverage", lines)
                    tp1 = extract_value("Target 1", lines) or extract_value("TP1", lines)
                    tp2 = extract_value("Target 2", lines) or extract_value("TP2", lines)
                    tp3 = extract_value("Target 3", lines) or extract_value("TP3", lines)
                    tp4 = extract_value("Target 4", lines) or extract_value("TP4", lines)
                    stop_loss = extract_value("Stop Loss", lines) or extract_value("SL", lines)

                    signal_buffer.append((
                        pair,
                        setup_type,
                        to_decimal_safe(entry),
                        int(to_decimal_safe(leverage.replace('x',''))) if leverage and leverage != "None" else None,
                        to_decimal_safe(tp1),
                        to_decimal_safe(tp2),
                        to_decimal_safe(tp3),
                        to_decimal_safe(tp4),
                        to_decimal_safe(stop_loss),
                        date,
                        text,
                        channel_name
                    ))

                    print(f"✅ Signal detected: {pair} {setup_type} from {channel_name}")
                else:
                    if event.message.sender:
                        sender = getattr(event.message.sender, "first_name", None) \
                                 or getattr(event.message.sender, "title", None) \
                                 or str(event.message.sender_id)
                    else:
                        sender = getattr(event.chat, "title", None) or str(event.chat_id)

                    market_buffer.append((sender, text, date))
                    print(f"📊 Market message from {sender}: {text[:100]}...")

                # Flush immediately if batch size reached
                if len(signal_buffer) >= BATCH_SIZE or len(market_buffer) >= BATCH_SIZE:
                    await flush_buffers()

                # Broadcast to WebSocket clients
                await broadcast_message(json.dumps({
                    "text": text,
                    "date": str(date),
                    "is_signal": is_signal,
                    "channel": channel_name
                }))

        except Exception as e:
            print(f"❌ Error processing message: {e}")

    print("👂 Listening for Telegram messages...")
    await client.run_until_disconnected()

# ----------------------------
# Main
# ----------------------------
async def main():
    try:
        if not DB_URL:
            print("❌ DATABASE_URL environment variable is required")
            return

        # Create tables once at startup
        await create_tables()

        # Start background tasks
        asyncio.create_task(flush_buffers())
        asyncio.create_task(start_websocket_server())

        # Start Telegram client
        await run_telegram_client()

    except Exception as e:
        print(f"💥 Fatal error: {e}")
    finally:
        print("🛑 Shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
