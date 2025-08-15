import os
import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed
from telethon import TelegramClient, events
from urllib.parse import urlparse
from dotenv import load_dotenv
from psycopg2.pool import SimpleConnectionPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))

# Database connection pool
db_url = os.getenv("DATABASE_URL")
url = urlparse(db_url)
db_config = {
    'dbname': url.path[1:],  # Remove leading /
    'user': url.username,
    'password': url.password,
    'host': url.hostname,
    'port': url.port,
    'sslmode': 'require'
}
db_pool = SimpleConnectionPool(1, 20, **db_config)

# Helper function for safe numeric conversion
def to_float_safe(value):
    if not value:
        return None
    try:
        cleaned = ''.join(c for c in value if c.isdigit() or c in ('.', '-'))
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

# Table creation
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
            logger.info("Checked/Created: signal_messages table")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_messages (
                    id SERIAL PRIMARY KEY,
                    sender VARCHAR(50),
                    text TEXT,
                    timestamp TIMESTAMP
                );
            """)
            logger.info("Checked/Created: market_messages table")
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        conn.rollback()
    finally:
        db_pool.putconn(conn)

# WebSocket handling
connected_clients = set()
MAX_CONNECTIONS = 100

async def websocket_handler(websocket):
    if len(connected_clients) >= MAX_CONNECTIONS:
        logger.warning("Max connections reached, rejecting new connection")
        await websocket.close(code=1008, reason="Max connections reached")
        return
    logger.info("WebSocket client connected")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            logger.debug(f"Received message: {message}")
    except ConnectionClosed as e:
        logger.warning(f"WebSocket connection closed: {e}")
    except asyncio.exceptions.IncompleteReadError as e:
        logger.warning(f"Incomplete read error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info("WebSocket client disconnected")

async def send_to_clients(data):
    if connected_clients:
        message = json.dumps(data, default=str)
        tasks = [client.send(message) for client in connected_clients]
        await asyncio.gather(*tasks, return_exceptions=True)

# Improved value extractor
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
            logger.info(f"Saved signal for pair: {pair}")
    except Exception as e:
        logger.error(f"Failed to save signal: {e}, pair={pair}, entry={entry}, leverage={leverage}")
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
            logger.info("Saved market message")
    except Exception as e:
        logger.error(f"Failed to save market message: {e}")
        conn.rollback()
    finally:
        db_pool.putconn(conn)

# Telegram listener
async def telegram_handler():
    client = TelegramClient('session', API_ID, API_HASH)
    try:
        await client.start()
        logger.info("Telegram client started")
    except Exception as e:
        logger.error(f"Failed to start Telegram client: {e}")
        return

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
                logger.info(f"Detected signal message at {date}")
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
                logger.info(f"Detected market message at {date}")
                sender = event.message.sender.first_name if event.message.sender else "Unknown"
                save_market(sender, text, date)
                await send_to_clients({
                    "type": "market",
                    "sender": sender,
                    "text": text,
                    "timestamp": date.isoformat()
                })

        except Exception as e:
            logger.error(f"Error processing message: {e}\nMessage: {text}")

    await client.run_until_disconnected()

# Main function
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
    logger.info("WebSocket server started on wss://telegramsignals-production.up.railway.app")

    try:
        await telegram_handler()
    finally:
        server.close()
        await server.wait_closed()
        db_pool.closeall()
        logger.info("Server and database pool closed")

if __name__ == "__main__":
    asyncio.run(main())