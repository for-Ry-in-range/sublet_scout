from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from app.routes import apartments
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# testing with just a user model rn
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(200), unique=True)

# create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(apartments.router)

@app.get("/")
def root():
    return {"message": "Connected to Neon PostgreSQL successfully!"}

@app.post("/add_dummy")
def add_dummy_user():
    session = SessionLocal()
    new_user = User(name="Ada Lovelace", email="ada_lovelace@example.com")
    session.add(new_user)
    session.commit()
    session.close()
    return {"status": "added", "user": {"name": "Ada Lovelace", "email": "ada_lovelace@example.com"}}

@app.get("/users")
def list_users():
    session = SessionLocal()
    users = session.query(User).all()
    result = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
    session.close()
    return result

