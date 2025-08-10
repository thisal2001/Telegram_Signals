import os
import asyncio
import json
from telethon import TelegramClient, events
import websockets
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

# Database connection with auto-reconnect
def connect_db():
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                host=DB_HOST,
                port=DB_PORT,
                sslmode="require",
                connect_timeout=5
            )
            logger.info("✅ Successfully connected to database")
            return conn
        except Exception as e:
            logger.error(f"⚠️ Failed to connect to database (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

db = connect_db()

def get_db_connection():
    global db
    try:
        with db.cursor() as cur:
            cur.execute("SELECT 1;")
        return db
    except Exception as e:
        logger.error(f"🔄 Reconnecting to DB... Error: {e}")
        db = connect_db()
        return db

# Helper function for safe numeric conversion
def to_float_safe(value):
    """Convert string to float, handling emojis and special characters"""
    if not value:
        return None
    try:
        # Remove all non-numeric characters except . and -
        cleaned = ''.join(c for c in value if c.isdigit() or c in ('.', '-'))
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

# Table creation with numeric columns
def create_tables():
    conn = get_db_connection()
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
            logger.info("✅ Checked/Created: signal_messages table")

            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS market_messages (
                                                                          id SERIAL PRIMARY KEY,
                                                                          sender VARCHAR(50),
                               text TEXT,
                               timestamp TIMESTAMP
                               );
                           """)
            logger.info("✅ Checked/Created: market_messages table")
            conn.commit()
    except Exception as e:
        logger.error(f"⚠️ Failed to create tables: {e}")
        conn.rollback()
        raise

# WebSocket handling
connected_clients = set()

async def websocket_handler(websocket):
    client_id = id(websocket)
    logger.info(f"✅ WebSocket client connected (ID: {client_id})")
    connected_clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"❌ WebSocket client disconnected normally (ID: {client_id})")
    except Exception as e:
        logger.error(f"❌ WebSocket client disconnected with error (ID: {client_id}): {e}")
    finally:
        connected_clients.discard(websocket)

async def send_to_clients(data):
    if not connected_clients:
        return

    message = json.dumps(data, default=str)
    for client in connected_clients.copy():  # Use a copy to avoid modification during iteration
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            connected_clients.discard(client)
            logger.info("❌ Removed disconnected client")
        except Exception as e:
            logger.error(f"⚠️ Error sending to client: {e}")
            connected_clients.discard(client)

# Improved value extractor with emoji handling
def extract_value(label, lines):
    for line in lines:
        if label.lower() in line.lower():
            parts = line.split(":")
            if len(parts) > 1:
                value = parts[1].strip().replace("•", "").strip()
                # Special handling for stop loss (remove ☠️)
                if "stop loss" in label.lower() or "sl" in label.lower():
                    value = value.split('☠️')[0].strip()
                return value
    return None

# Save function with robust numeric conversion
def save_signal(pair, setup_type, entry, leverage, tp1, tp2, tp3, tp4, stop_loss, timestamp, full_message):
    conn = get_db_connection()
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
            logger.info(f"✅ Saved signal for {pair}")
    except Exception as e:
        logger.error(f"⚠️ Failed to save signal: {e}\nProblem values: "
                     f"entry={entry}, leverage={leverage}, stop_loss={stop_loss}")
        conn.rollback()

def save_market(sender, text, timestamp):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                           INSERT INTO market_messages (sender, text, timestamp)
                           VALUES (%s,%s,%s)
                           """, (sender, text, timestamp))
            conn.commit()
            logger.info("✅ Saved market message")
    except Exception as e:
        logger.error(f"⚠️ Failed to save market message: {e}")
        conn.rollback()

def get_sender_name(message):
    """Get sender name from message with fallbacks"""
    if not message.sender:
        return "Unknown"

    if hasattr(message.sender, 'first_name'):
        return message.sender.first_name
    elif hasattr(message.sender, 'title'):
        return message.sender.title
    elif hasattr(message.sender, 'username'):
        return f"@{message.sender.username}"
    return "Unknown"

# Telegram listener with improved error handling
async def telegram_handler():
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            client = TelegramClient('session', API_ID, API_HASH)
            await client.start()
            logger.info("✅ Telegram client started.")
            break
        except Exception as e:
            logger.error(f"⚠️ Failed to start Telegram client (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                raise

    @client.on(events.NewMessage(chats=GROUP_ID))
    async def handler(event):
        try:
            text = event.message.message
            date = event.message.date

            if not text:
                return

            lines = [line.strip() for line in text.splitlines() if line.strip()]

            is_signal = (
                    any(line.startswith('#') for line in lines) and
                    any('entry' in line.lower() for line in lines) and
                    any('profit' in line.lower() for line in lines) and
                    any('loss' in line.lower() for line in lines)
            )

            if is_signal:
                logger.info(f"[Signal] Detected signal message at {date}")
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

                save_signal(
                    pair, setup_type, entry, leverage,
                    tp1, tp2, tp3, tp4, stop_loss,
                    date, text
                )

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
                logger.info(f"[Market] Detected market message at {date}")
                sender = get_sender_name(event.message)
                save_market(sender, text, date)
                await send_to_clients({
                    "type": "market",
                    "sender": sender,
                    "text": text,
                    "timestamp": date.isoformat()
                })

        except Exception as e:
            logger.error(f"⚠️ Error processing message: {e}\nMessage: {text[:200]}...")

    try:
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"⚠️ Telegram client error: {e}")
        raise
    finally:
        await client.disconnect()
        logger.info("Telegram client disconnected")

# Main function
async def main():
    try:
        create_tables()

        server = await websockets.serve(
            websocket_handler,
            "0.0.0.0",
            6789,
            ping_interval=20,
            ping_timeout=60
        )
        logger.info("🚀 WebSocket server started on wss://telegramsignals-production.up.railway.app")

        await telegram_handler()
    except asyncio.CancelledError:
        logger.info("🛑 Received shutdown signal")
    except Exception as e:
        logger.error(f"⚠️ Fatal error: {e}")
    finally:
        if 'server' in locals():
            server.close()
            await server.wait_closed()
            logger.info("WebSocket server stopped")
        if 'db' in globals():
            db.close()
            logger.info("Database connection closed")
        logger.info("🛑 Application shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Keyboard interrupt received")
    except Exception as e:
        logger.error(f"⚠️ Unhandled error: {e}")