from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# This acts as your "Database"
users_db = []

# Data model based on your JSON structure
class User(BaseModel):
    id: str
    user: str
    mail: str
    password: str  # Renamed from 'pass' because 'pass' is a reserved keyword in Python
    full_name: str
    stack: str
    wanted_stack: str
    abt_me: str
    additional_links: str
    swipe_rate: int = 0
    feed_appearances: int = 0
    swipes_yes: int = 0
    swiped_on: int = 0

# 1. Register: Create a new user
@app.post("/users")
def register_user(user: User):
    # Check if user ID already exists
    if any(u["id"] == user.id for u in users_db):
        raise HTTPException(status_code=400, detail="User ID already exists")
    
    users_db.append(user.dict())
    return {"message": "User registered successfully", "user": user}

# 2. Login: Simple check for mail and password
@app.post("/login")
def login(credentials: dict):
    email = credentials.get("mail")
    password = credentials.get("pass")
    
    user = next((u for u in users_db if u["mail"] == email and u["password"] == password), None)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return {"message": "Login successful", "user": user}

# 3. Edit: Update user info by ID
@app.put("/users/{user_id}")
def update_user(user_id: str, updated_data: dict):
    for user in users_db:
        if user["id"] == user_id:
            user.update(updated_data)
            return {"message": "User updated", "user": user}
    
    raise HTTPException(status_code=404, detail="User not found")

# 4. Get all (to see your "MockAPI" data)
@app.get("/users")
def get_all_users():
    return users_db
