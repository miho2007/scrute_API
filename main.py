import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List

# --- DATABASE CONFIGURATION ---
# Render provides DATABASE_URL. If it's missing (local), we use SQLite.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./local.db"

# Connect to Postgres (or SQLite)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- DATABASE MODEL ---
class UserTable(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    user = Column(String)
    mail = Column(String, unique=True, index=True)
    password = Column(String)  # This maps to the "pass" field in your JSON
    full_name = Column(String)
    stack = Column(String)
    wanted_stack = Column(String)
    abt_me = Column(String)
    additional_links = Column(String)
    swipe_rate = Column(Integer, default=0)
    feed_appearances = Column(Integer, default=0)
    swipes_yes = Column(Integer, default=0)
    swiped_on = Column(Integer, default=0)

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# --- FASTAPI APP SETUP ---
app = FastAPI(title="Miho Backend API")

# Dependency to get database access in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- DATA SCHEMAS (Pydantic) ---
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

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "API is online", "docs": "/docs"}

# 1. Register
@app.post("/users", response_model=UserSchema)
def register(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(UserTable).filter(UserTable.mail == user.mail).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    new_user = UserTable(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# 2. Login (Checks mail and pass)
@app.post("/login")
def login(credentials: dict, db: Session = Depends(get_db)):
    email = credentials.get("mail")
    password = credentials.get("pass")
    
    user = db.query(UserTable).filter(
        UserTable.mail == email, 
        UserTable.password == password
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

# 3. Edit User
@app.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: str, updated_data: dict, db: Session = Depends(get_db)):
    db_user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in updated_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# 4. Get All Users (MockAPI style)
@app.get("/users", response_model=List[UserSchema])
def get_all(db: Session = Depends(get_db)):
    return db.query(UserTable).all()
