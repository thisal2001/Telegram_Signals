import os
import asyncio
import json
from telethon import TelegramClient, events
import websockets
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))

# Parse DATABASE_URL
db_url = os.getenv("DATABASE_URL")
url = urlparse(db_url)

DB_NAME = url.path[1:]  # remove leading /
DB_USER = url.username
DB_PASS = url.password
DB_HOST = url.hostname
DB_PORT = url.port

# Connect to Neon PostgreSQL
db = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT,
    sslmode="require"  # Neon requires SSL
)
cursor = db.cursor()

# Create tables if not exist
cursor.execute("""
               CREATE TABLE IF NOT EXISTS signal_messages (
                                                              id SERIAL PRIMARY KEY,
                                                              pair VARCHAR(50),
                   setup_type VARCHAR(10),
                   entry VARCHAR(50),
                   leverage VARCHAR(50),
                   tp1 VARCHAR(50),
                   tp2 VARCHAR(50),
                   tp3 VARCHAR(50),
                   tp4 VARCHAR(50),
                   timestamp TIMESTAMP,
                   full_message TEXT
                   );
               """)

cursor.execute("""
               CREATE TABLE IF NOT EXISTS market_messages (
                                                              id SERIAL PRIMARY KEY,
                                                              sender VARCHAR(50),
                   text TEXT,
                   timestamp TIMESTAMP
                   );
               """)
db.commit()

connected_clients = set()

# WebSocket handler
async def websocket_handler(websocket):
    print("✅ WebSocket client connected")
    connected_clients.add(websocket)
    try:
        async for _ in websocket:  # Keep connection alive
            pass
    except:
        pass
    finally:
        connected_clients.remove(websocket)
        print("❌ WebSocket client disconnected")

# Broadcast to all connected clients
async def send_to_clients(data):
    if connected_clients:
        message = json.dumps(data, default=str)
        await asyncio.gather(*[client.send(message) for client in connected_clients])

# Helper: extract value by label
def extract_value(label, lines):
    for line in lines:
        if label in line:
            parts = line.split(":")
            if len(parts) > 1:
                return parts[1].strip()
    return None

# Save signal message
def save_signal(pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, timestamp, full_message):
    cursor.execute("""
                   INSERT INTO signal_messages (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, timestamp, full_message)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   """, (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, timestamp, full_message))
    db.commit()

# Save market message
def save_market(sender, text, timestamp):
    cursor.execute("""
                   INSERT INTO market_messages (sender, text, timestamp)
                   VALUES (%s,%s,%s)
                   """, (sender, text, timestamp))
    db.commit()

# Telegram listener
async def telegram_handler():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start()
    print("✅ Telegram client started.")

    @client.on(events.NewMessage(chats=GROUP_ID))
    async def handler(event):
        try:
            text = event.message.message
            date = event.message.date  # datetime object
            lines = text.splitlines()

            # Identify if it's a signal message
            is_signal = (
                    '#' in text and
                    'Entry' in text and
                    'Take Profit' in text and
                    'Stop Loss' in text
            )

            if is_signal:
                print("[Signal] Detected signal message!")

                first_line = lines[0] if lines else ""
                pair = first_line.split()[0].strip('#') if first_line else "UNKNOWN"
                setup_type = "LONG" if "LONG" in first_line.upper() else "SHORT" if "SHORT" in first_line.upper() else "UNKNOWN"

                entry = extract_value("Entry", lines)
                leverage = extract_value("Leverage", lines)
                tp1 = extract_value("Target 1", lines)
                tp2 = extract_value("Target 2", lines)
                tp3 = extract_value("Target 3", lines)
                tp4 = extract_value("Target 4", lines)

                # Save to DB
                save_signal(pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, date, text)

                # Send to WebSocket clients
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
                    "timestamp": date,
                    "full_message": text
                })

            else:
                print("[Market] Detected market message.")
                save_market("Telegram", text, date)

                await send_to_clients({
                    "type": "market",
                    "sender": "Telegram",
                    "text": text,
                    "timestamp": date
                })

        except Exception as e:
            print(f"[Error] Failed to process message: {e}")

    await client.run_until_disconnected()

# Main entry point
async def main():
    server = await websockets.serve(websocket_handler, "0.0.0.0", 6789)
    print("🚀 WebSocket server started on ws://localhost:6789")
    await telegram_handler()

if __name__ == "__main__":
    asyncio.run(main())
