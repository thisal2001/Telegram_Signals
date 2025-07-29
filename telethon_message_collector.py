import os
import asyncio
import json
from telethon import TelegramClient, events
import websockets
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
GROUP_ID = int(os.getenv("GROUP_ID"))

connected_clients = set()

# WebSocket handler
async def websocket_handler(websocket):
    print("✅ WebSocket client connected")
    connected_clients.add(websocket)
    try:
        async for _ in websocket:  # Keep connection alive (no incoming messages expected)
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

# Helper: extract value by label (e.g., "Entry:", "Leverage:")
def extract_value(label, lines):
    for line in lines:
        if label in line:
            parts = line.split(":")
            if len(parts) > 1:
                return parts[1].strip()
    return None

# Telegram listener
async def telegram_handler():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start()
    print("✅ Telegram client started.")

    @client.on(events.NewMessage(chats=GROUP_ID))
    async def handler(event):
        try:
            text = event.message.message
            date = event.message.date.isoformat()
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

                # Send signal message to WebSocket clients
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
                # Send market message to WebSocket clients
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
