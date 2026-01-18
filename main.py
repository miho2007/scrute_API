import os
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# 1. Database Configuration
# Render provides the DB URL in an environment variable named 'DATABASE_URL'
# We use SQLite as a fallback for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# Fix for SQLAlchemy: Postgres URLs must start with "postgresql://" (Render sometimes gives "postgres://")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Database Table Model (Same as before)
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

# Create tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schema
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

# --- API ENDPOINTS (Stay the same) ---
@app.post("/users")
def register_user(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(UserTable).filter(UserTable.id == user.id).first()
    if db_user: raise HTTPException(status_code=400, detail="User already exists")
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
    if not user: raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@app.put("/users/{user_id}")
def update_user(user_id: str, updated_data: dict, db: Session = Depends(get_db)):
    db_user = db.query(UserTable).filter(UserTable.id == user_id).first()
    if not db_user: raise HTTPException(status_code=404, detail="User not found")
    for key, value in updated_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    return db.query(UserTable).all()
