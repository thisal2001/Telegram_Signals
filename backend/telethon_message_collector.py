import os
import asyncio
import json
from telethon import TelegramClient, events
from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool
from urllib.parse import urlparse
import websockets
from websockets.exceptions import ConnectionClosed

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))
DB_URL = os.getenv("DATABASE_URL")

# Database connection pool
url = urlparse(DB_URL)
db_config = {
    'dbname': url.path[1:],  # remove leading /
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port,
    'sslmode': 'require'
}
db_pool = SimpleConnectionPool(1, 20, **db_config)

# WebSocket clients
connected_clients = set()
MAX_CONNECTIONS = 100

# Helper for numeric conversion
def to_float_safe(value):
    if not value:
        return None
    try:
        cleaned = ''.join(c for c in value if c.isdigit() or c in ('.', '-'))
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

# Create tables if not exist
def create_tables():
    conn = db_pool.getconn()
    try:
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
                    full_message TEXT
                );
            """)
            print("Checked/Created: signal_messages table")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_messages (
                    id SERIAL PRIMARY KEY,
                    sender VARCHAR(50),
                    text TEXT,
                    timestamp TIMESTAMP
                );
            """)
            print("Checked/Created: market_messages table")
            conn.commit()
    except Exception as e:
        print(f"Failed to create tables: {e}")
        conn.rollback()
    finally:
        db_pool.putconn(conn)

# WebSocket handler
async def websocket_handler(ws):
    if len(connected_clients) >= MAX_CONNECTIONS:
        await ws.close(code=1008, reason="Max connections reached")
        return
    connected_clients.add(ws)
    print("WebSocket client connected")
    try:
        async for msg in ws:
            print(f"Received message from client: {msg}")
    except ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")
    finally:
        connected_clients.remove(ws)
        print("WebSocket client disconnected")

async def send_to_clients(data):
    if connected_clients:
        message = json.dumps(data, default=str)
        tasks = [client.send(message) for client in connected_clients]
        await asyncio.gather(*tasks, return_exceptions=True)

# Extract value from lines
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

# Save functions
def save_signal(pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO signal_messages (
                    pair, setup_type, entry, leverage,
                    tp1, tp2, tp3, tp4, stop_loss,
                    timestamp, full_message
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pair, setup_type,
                to_float_safe(entry),
                int(to_float_safe(leverage.replace('x', ''))) if leverage else None,
                to_float_safe(tp1),
                to_float_safe(tp2),
                to_float_safe(tp3),
                to_float_safe(tp4),
                to_float_safe(stop_loss),
                timestamp,
                full_message
            ))
            conn.commit()
            print(f"Saved signal: {pair}")
    except Exception as e:
        print(f"Failed to save signal: {e}")
        conn.rollback()
    finally:
        db_pool.putconn(conn)

def save_market(sender, text, timestamp):
    conn = db_pool.getconn()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO market_messages (sender, text, timestamp)
                VALUES (%s,%s,%s)
            """, (sender, text, timestamp))
            conn.commit()
            print(f"Saved market message from {sender}")
    except Exception as e:
        print(f"Failed to save market message: {e}")
        conn.rollback()
    finally:
        db_pool.putconn(conn)

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
                print(f"Signal message detected at {date}")
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

                save_signal(pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, date, text)
                await send_to_clients({
                    "type": "signal",
                    "pair": pair,
                    "setup_type": setup_type,
                    "entry": entry,
                    "leverage": leverage,
                    "tp1": tp1,
                    "tp2": tp2,
                    "tp3": tp3,
                    "tp4": tp4,
                    "stop_loss": stop_loss,
                    "timestamp": date.isoformat(),
                    "full_message": text
                })
            else:
                sender = event.message.sender.first_name if event.message.sender else "Unknown"
                print(f"Market message detected at {date}")
                save_market(sender, text, date)
                await send_to_clients({
                    "type": "market",
                    "sender": sender,
                    "text": text,
                    "timestamp": date.isoformat()
                })
        except Exception as e:
            print(f"Error processing message: {e}\nMessage: {text}")

    await client.run_until_disconnected()

# Main
async def main():
    create_tables()
    server = await websockets.serve(
        websocket_handler,
        "0.0.0.0",
        6789,
        ping_interval=20,
        ping_timeout=120,
        max_size=1000000
    )
    print("WebSocket server started")

    try:
        await run_telegram_client("session")  # uses your session.session file
    finally:
        server.close()
        await server.wait_closed()
        db_pool.closeall()
        print("Server and database pool closed")

if __name__ == "__main__":
    asyncio.run(main())
