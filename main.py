from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://chat_db_crwr_user:ghR4USGp12sMVl0LcDxErzn3gZ2fnKCE@dpg-d544gqf5r7bs73e736p0-a/chat_db_crwr"
)
database = Database(DATABASE_URL)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await database.connect()
    # create messages table
    await database.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            text TEXT NOT NULL
        )
    """)
    # create swipes table
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

# New endpoint: save swipe
@app.post("/swipe")
async def save_swipe(data: dict):
    swiper_id = data.get("swiper_id")
    swiped_id = data.get("swiped_id")
    if not swiper_id or not swiped_id:
        return {"error": "Missing swiper_id or swiped_id"}

    query = """
        INSERT INTO swipes (swiper_id, swiped_id)
        VALUES (:swiper_id, :swiped_id)
        ON CONFLICT (swiper_id, swiped_id) DO NOTHING
    """
    await database.execute(query, values={"swiper_id": swiper_id, "swiped_id": swiped_id})
    return {"status": "ok", "swiper_id": swiper_id, "swiped_id": swiped_id}
