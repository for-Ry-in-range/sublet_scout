from fastapi import FastAPI
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.listing import Listing
#from app.routes import apartments

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
#app.include_router(apartments.router)

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
    return {"status": "added"}

@app.get("/users")
def list_users():
    session = SessionLocal()
    users = session.query(User).all()
    result = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
    session.close()
    return result
