from fastapi import FastAPI
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Import your two main functions
import telethon_message_collector
from fetch_past_messages import fetch_past_messages
from fastapi import FastAPI, WebSocket



app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://telegram-signals-lac.vercel.app"],  # exact frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Start real-time Telegram message collector in background
    asyncio.create_task(telethon_message_collector.main())
    print("Telegram message collector started on FastAPI startup.")

@app.get("/fetch-past")
async def fetch_past_endpoint():
    await fetch_past_messages()  # ✅ must be awaited
    return {"status": "success", "message": "Fetched past messages"}

# Separate WebSocket route
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket client connected")
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception as e:
        print("WebSocket disconnected:", e)

