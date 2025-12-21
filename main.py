from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from databases import Database
import os

# -----------------------
# Database
# -----------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://chat_db_crwr_user:ghR4USGp12sMVl0LcDxErzn3gZ2fnKCE@dpg-d544gqf5r7bs73e736p0-a/chat_db_crwr"
)
database = Database(DATABASE_URL)

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for testing; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Pydantic models
# -----------------------
class Message(BaseModel):
    sender_id: int
    receiver_id: int
    text: str

class Swipe(BaseModel):
    swiper_id: int
    swiped_id: int

# -----------------------
# Startup / Shutdown
# -----------------------
@app.on_event("startup")
async def startup():
    await database.connect()
    # messages table
    await database.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT NOT NULL
        )
    """)
    # swipes table
    await database.execute("""
        CREATE TABLE IF NOT EXISTS swipes (
            id SERIAL PRIMARY KEY,
            swiper_id INTEGER NOT NULL,
            swiped_id INTEGER NOT NULL,
            UNIQUE (swiper_id, swiped_id)
        )
    """)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# -----------------------
# Chat endpoints
# -----------------------
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

# -----------------------
# Swipe endpoints
# -----------------------
@app.post("/swipe")
async def save_swipe(swipe: Swipe):
    query = """
        INSERT INTO swipes (swiper_id, swiped_id)
        VALUES (:swiper_id, :swiped_id)
        ON CONFLICT (swiper_id, swiped_id) DO NOTHING
    """
    try:
        await database.execute(query, values=swipe.dict())
        return {"status": "ok", "swiper_id": swipe.swiper_id, "swiped_id": swipe.swiped_id}
    except Exception as e:
        return {"error": str(e)}

@app.get("/swipes/{user_id}")
async def get_swiped_users(user_id: int):
    query = """
        SELECT u.id, u.user, u.stack, u.abt_me, u.additional_links
        FROM swipes s
        JOIN users u ON u.id = s.swiped_id
        WHERE s.swiper_id = :user_id
    """
    try:
        rows = await database.fetch_all(query, values={"user_id": user_id})
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}
