from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Allow front-end to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Message model
class Message(BaseModel):
    sender_id: int
    receiver_id: int
    text: str

# In-memory storage
messages: List[Message] = []

@app.post("/send")
def send_message(msg: Message):
    messages.append(msg)
    return {"status": "ok", "message": msg}

@app.get("/messages/{user_id}")
def get_messages(user_id: int):
    # return messages where user is sender or receiver
    user_msgs = [m for m in messages if m.sender_id == user_id or m.receiver_id == user_id]
    return user_msgs
