import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List

# --- DATABASE CONFIGURATION ---
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix 1: Ensure it starts with postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Fix 2: Append SSL mode to the string if it's not already there
    if "sslmode" not in DATABASE_URL and "localhost" not in DATABASE_URL:
        if "?" in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
        else:
            DATABASE_URL += "?sslmode=require"

# Create Engine with specific SSL arguments for Render
engine = create_engine(
    DATABASE_URL if DATABASE_URL else "sqlite:///./local.db",
    connect_args={"sslmode": "require"} if DATABASE_URL and "localhost" not in DATABASE_URL else {},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DATABASE MODEL ---
class UserTable(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    user = Column(String)
    mail = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)
    stack = Column(String)
    wanted_stack = Column(String)
    abt_me = Column(String)
    additional_links = Column(String)
    swipe_rate = Column(Integer, default=0)
    feed_appearances = Column(Integer, default=0)
    swipes_yes = Column(Integer, default=0)
    swiped_on = Column(Integer, default=0)

# This line is where the error triggers; we'll wrap it in a try/except for better logging
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"CRITICAL DATABASE ERROR: {e}")

app = FastAPI(title="Miho Final Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserSchema(BaseModel):
    id: str
    user: str
    mail: str
    password: str
    full_name: str
    stack: str
    wanted_stack: str
    abt_me: str
    additional_links: str
    swipe_rate: int = 0
    feed_appearances: int = 0
    swipes_yes: int = 0
    swiped_on: int = 0
    class Config:
        from_attributes = True

@app.get("/")
def health():
    return {"status": "online", "db": "connected"}

@app.post("/users", response_model=UserSchema)
def register(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(UserTable).filter(UserTable.mail == user.mail).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User exists")
    new_user = UserTable(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(credentials: dict, db: Session = Depends(get_db)):
    user = db.query(UserTable).filter(
        UserTable.mail == credentials.get("mail"),
        UserTable.password == credentials.get("pass")
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@app.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: str, updated_data: dict, db: Session = Depends(get_db)):
    db_user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Not found")
    for key, value in updated_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[UserSchema])
def get_all(db: Session = Depends(get_db)):
    return db.query(UserTable).all()
