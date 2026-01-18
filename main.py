import os
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel
from typing import List

# ======================================================
# DATABASE CONFIG
# ======================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # Ensure SSL
    if "sslmode" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"

# Create engine
engine = create_engine(
    DATABASE_URL if DATABASE_URL else "sqlite:///./local.db",
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ======================================================
# DATABASE MODEL
# ======================================================

class UserTable(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    user = Column(String, nullable=False)
    mail = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String)
    stack = Column(String)
    wanted_stack = Column(String)
    abt_me = Column(String)
    additional_links = Column(String)
    swipe_rate = Column(Integer, default=0)
    feed_appearances = Column(Integer, default=0)
    swipes_yes = Column(Integer, default=0)
    swiped_on = Column(Integer, default=0)

# ======================================================
# SAFELY CREATE TABLES
# ======================================================

# Retry connecting if DB is not ready yet
retries = 5
for i in range(retries):
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        break
    except OperationalError as e:
        print(f"⚠️ Database connection failed (attempt {i+1}/{retries}): {e}")
        time.sleep(3)
else:
    print("❌ Could not connect to the database after several attempts")

# ======================================================
# FASTAPI APP
# ======================================================

app = FastAPI(title="Miho Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
# DEPENDENCIES
# ======================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================================================
# SCHEMAS
# ======================================================

class UserCreate(BaseModel):
    id: str
    user: str
    mail: str
    password: str
    full_name: str
    stack: str
    wanted_stack: str
    abt_me: str
    additional_links: str

class UserResponse(UserCreate):
    swipe_rate: int
    feed_appearances: int
    swipes_yes: int
    swiped_on: int

    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    mail: str
    password: str

# ======================================================
# ROUTES
# ======================================================

@app.get("/")
def health():
    return {"status": "online"}

@app.post("/users", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(UserTable).filter(UserTable.mail == user.mail).first():
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = UserTable(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=UserResponse)
def login(credentials: LoginSchema, db: Session = Depends(get_db)):
    user = db.query(UserTable).filter(
        UserTable.mail == credentials.mail,
        UserTable.password == credentials.password
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return user

@app.get("/users", response_model=List[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(UserTable).all()

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: str, data: dict, db: Session = Depends(get_db)):
    user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user
