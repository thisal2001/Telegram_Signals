from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

# Enable CORS so your frontend can call backend without being blocked by browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import your existing fetch_past_messages function here
from fetch_past_messages import fetch_past_messages

@app.get("/fetch-past")
async def fetch_past_endpoint():
    # Run your async fetcher and wait for it to complete
    await fetch_past_messages()
    return {"status": "success", "message": "Fetched past messages from Telegram"}
