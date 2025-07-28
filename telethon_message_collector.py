import os
import json
import asyncio
from telethon import TelegramClient, events
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
import websockets

# Load environment variables
load_dotenv()

# Telegram API credentials
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
group_id = int(os.getenv("GROUP_ID"))

# Parse PostgreSQL URL
pg_url = urlparse(os.getenv("DATABASE_URL"))
db = psycopg2.connect(
    dbname=pg_url.path[1:],
    user=pg_url.username,
    password=pg_url.password,
    host=pg_url.hostname,
    port=pg_url.port,
    sslmode=parse_qs(pg_url.query).get("sslmode", ["require"])[0]
)
cursor = db.cursor()

# Create tables if they don't exist
cursor.execute("""
               CREATE TABLE IF NOT EXISTS signals (
                                                      id SERIAL PRIMARY KEY,
                                                      pair VARCHAR(50),
                   setup_type VARCHAR(10),
                   entry VARCHAR(20),
                   leverage VARCHAR(10),
                   tp1 VARCHAR(20),
                   tp2 VARCHAR(20),
                   tp3 VARCHAR(20),
                   tp4 VARCHAR(20),
                   timestamp TIMESTAMP,
                   full_message TEXT
                   )
               """)

cursor.execute("""
               CREATE TABLE IF NOT EXISTS market_messages (
                                                              id SERIAL PRIMARY KEY,
                                                              sender VARCHAR(255),
                   text TEXT,
                   date TIMESTAMP
                   )
               """)
db.commit()

# Initialize Telegram client
client = TelegramClient('session', api_id, api_hash)

# WebSocket clients
connected_clients = set()

# WebSocket handler
async def websocket_handler(websocket, path):
    connected_clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_clients.remove(websocket)

# Helper to extract value by label
def extract_value(label, lines):
    for line in lines:
        if label in line:
            parts = line.split(":")
            if len(parts) > 1:
                return parts[1].strip()
    return None

# Broadcast message to WebSocket clients
async def broadcast(message):
    if connected_clients:
        await asyncio.wait([ws.send(json.dumps(message)) for ws in connected_clients])

# Telegram message handler
@client.on(events.NewMessage(chats=group_id))
async def handler(event):
    try:
        sender = await event.get_sender()

        # ✅ Handle user vs channel sender
        if hasattr(sender, 'username') and sender.username:
            sender_name = sender.username
        elif hasattr(sender, 'first_name') and sender.first_name:
            sender_name = sender.first_name
        elif hasattr(sender, 'title'):  # Channel case
            sender_name = sender.title
        else:
            sender_name = 'Unknown'

        text = event.message.message
        date = event.message.date
        lines = text.splitlines()

        # Detect signal message
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
            cursor.execute("""
                           INSERT INTO signals (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, timestamp, full_message)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           """, (pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, date, text))
            db.commit()

            # Send via WebSocket
            await broadcast({
                "type": "signal",
                "pair": pair,
                "setup_type": setup_type,
                "entry": entry,
                "leverage": leverage,
                "tp1": tp1,
                "tp2": tp2,
                "tp3": tp3,
                "tp4": tp4,
                "timestamp": str(date),
                "full_message": text
            })

        else:
            print("[Market] Detected market message.")

            cursor.execute(
                "INSERT INTO market_messages (sender, text, date) VALUES (%s, %s, %s)",
                (sender_name, text, date)
            )
            db.commit()

            await broadcast({
                "type": "market",
                "sender": sender_name,
                "text": text,
                "timestamp": str(date)
            })

    except Exception as e:
        print(f"[Error] Failed to process message: {e}")

# Main async runner
async def main():
    # Start WebSocket server
    ws_server = await websockets.serve(websocket_handler, "0.0.0.0", 6789)
    print("WebSocket server started on ws://localhost:6789")

    # Start Telegram client
    await client.start()
    print("Telegram client started.")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
