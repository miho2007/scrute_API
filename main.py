from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from databases import Database
from typing import List
import os

# Use your Renderer PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://chat_db_crwr_user:ghR4USGp12sMVl0LcDxErzn3gZ2fnKCE@dpg-d544gqf5r7bs73e736p0-a/chat_db_crwr"
)
database = Database(DATABASE_URL)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for testing; tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    sender_id: int
    receiver_id: int
    text: str

@app.on_event("startup")
async def startup():
    await database.connect()
    # Create messages table if it doesn't exist
    await database.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT NOT NULL
        )
    """)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/send")
async def send_message(msg: Message):
    query = """
        INSERT INTO messages (sender_id, receiver_id, text) 
        VALUES (:sender_id, :receiver_id, :text)
    """
    await database.execute(query, values=msg.dict())
    return {"status": "ok", "message": msg}

@app.get("/messages/{user_id}")
async def get_messages(user_id: int):
    query = """
        SELECT * FROM messages 
        WHERE sender_id = :user_id OR receiver_id = :user_id
        ORDER BY id ASC
    """
    rows = await database.fetch_all(query, values={"user_id": user_id})
    return [dict(r) for r in rows]
