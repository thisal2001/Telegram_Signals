import os
import asyncio
import json
from telethon import TelegramClient, events
from dotenv import load_dotenv
from urllib.parse import urlparse
import websockets
from websockets.exceptions import ConnectionClosed

# Load env
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))
DB_URL = os.getenv("DATABASE_URL")

# Parse DB URL
url = urlparse(DB_URL)
db_config = {
    'user': url.username,
    'password': url.password,
    'database': url.path[1:],
    'host': url.hostname,
    'port': url.port,
    'ssl': "require"
}

# WebSocket clients
connected_clients = set()
MAX_CONNECTIONS = 100

# Buffers for batch inserts
signal_buffer = []
market_buffer = []
BATCH_SIZE = 10
FLUSH_INTERVAL = 5  # seconds

# DB pool (global)
db_pool = None

def to_float_safe(value):
    if not value:
        return None
    try:
        cleaned = ''.join(c for c in value if c.isdigit() or c in ('.', '-'))
        return float(cleaned) if cleaned else None
    except ValueError:
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
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_signal_timestamp ON signal_messages(timestamp);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_market_timestamp ON market_messages(timestamp);")
        print("Tables checked/created with indexes")

# WebSocket handler
async def websocket_handler(ws):
    if len(connected_clients) >= MAX_CONNECTIONS:
        await ws.close(code=1008, reason="Max connections reached")
        return
    connected_clients.add(ws)
    print("WebSocket client connected")
    try:
        async for msg in ws:
            print(f"Received from client: {msg}")
    except ConnectionClosed:
        pass
    finally:
        connected_clients.remove(ws)
        print("WebSocket client disconnected")

async def send_to_clients(data):
    if connected_clients:
        message = json.dumps(data, default=str)
        await asyncio.gather(*[client.send(message) for client in connected_clients], return_exceptions=True)

# Flush buffers periodically
async def flush_buffers():
    global signal_buffer, market_buffer
    while True:
        await asyncio.sleep(FLUSH_INTERVAL)

        if not signal_buffer and not market_buffer:
            continue

        async with db_pool.acquire() as conn:
            try:
                if signal_buffer:
                    await conn.executemany("""
                        INSERT INTO signal_messages
                        (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                        ON CONFLICT (full_message) DO NOTHING
                    """, signal_buffer)
                    print(f"Flushed {len(signal_buffer)} signals")
                    signal_buffer = []

                if market_buffer:
                    await conn.executemany("""
                        INSERT INTO market_messages (sender, text, timestamp)
                        VALUES ($1,$2,$3)
                        ON CONFLICT (text) DO NOTHING
                    """, market_buffer)
                    print(f"Flushed {len(market_buffer)} markets")
                    market_buffer = []

            except Exception as e:
                print(f"Batch insert failed: {e}")

# Extract value
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

# Telegram client
async def run_telegram_client(session_name="session"):
    client = TelegramClient(session_name, API_ID, API_HASH)
    await client.start()
    print("Telegram client started")

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
                    int(to_float_safe(leverage.replace('x',''))) if leverage else None,
                    to_float_safe(tp1), to_float_safe(tp2),
                    to_float_safe(tp3), to_float_safe(tp4),
                    to_float_safe(stop_loss), date, text
                ))

                await send_to_clients({
                    "type": "signal", "pair": pair, "setup_type": setup_type,
                    "entry": entry, "leverage": leverage,
                    "tp1": tp1, "tp2": tp2, "tp3": tp3, "tp4": tp4,
                    "stop_loss": stop_loss,
                    "timestamp": date.isoformat(),
                    "full_message": text
                })

            else:
                sender = event.message.sender.first_name if event.message.sender else "Unknown"
                market_buffer.append((sender, text, date))

                await send_to_clients({
                    "type": "market", "sender": sender,
                    "text": text, "timestamp": date.isoformat()
                })
        except Exception as e:
            print(f"Error processing message: {e}\nMessage: {event.message.message}")

    await client.run_until_disconnected()

# Main
async def main():
    global db_pool
    import asyncpg

    # Create connection pool
    db_pool = await asyncpg.create_pool(**db_config, min_size=1, max_size=20)
    await create_tables()

    asyncio.create_task(flush_buffers())  # run buffer flusher
    server = await websockets.serve(
        websocket_handler, "0.0.0.0", 6789,
        ping_interval=20, ping_timeout=120, max_size=1000000
    )
    print("WebSocket server started")
    try:
        await run_telegram_client("session")
    finally:
        server.close()
        await server.wait_closed()
        await db_pool.close()
        print("Server and DB pool closed")

if __name__ == "__main__":
    asyncio.run(main())
