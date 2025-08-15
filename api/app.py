from fastapi import FastAPI
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Import your two main functions
from fetch_past_messages import fetch_past_messages

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # exact frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/fetch-past")
async def fetch_past_endpoint():
    await fetch_past_messages()  # ✅ must be awaited
    return {"status": "success", "message": "Fetched past messages"}


