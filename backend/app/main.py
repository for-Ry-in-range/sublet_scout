from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.listing import Listing
#from app.routes import apartments

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
#app.include_router(apartments.router)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "html"))
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="static")

@app.get("/health")
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

@app.get("/", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
