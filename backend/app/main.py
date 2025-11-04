from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.listing import Listing
#from app.routes import apartments

load_dotenv()

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

@app.get("/homepage", response_class=HTMLResponse)
def show_homepage(request: Request):
    session = SessionLocal()
    try:
        listings = session.query(Listing).all()
        
        listings_data = [
            {
                "id": l.id,
                "title": l.title,
                "city": l.city,
                "cost_per_month": l.cost_per_month
            } for l in listings
        ]
    finally:
        session.close()
    return templates.TemplateResponse("homepage.html", {"request": request, "listings": listings_data})


@app.get("/individual_apt", response_class=HTMLResponse)
async def render_individual_apt(request: Request):
    map_key = os.getenv("GOOGLE_MAP_KEY")
    print("MAP_KEY:", map_key)
    return templates.TemplateResponse("individual_apt.html", {"request": request, "map_key": map_key})

@app.get("/search", response_class=HTMLResponse)
def show_search(request: Request, q: str | None = None):
    map_key = os.getenv("GOOGLE_MAP_KEY")
    results = []
    if q:
        session = SessionLocal()
        try:
            # Basic case-insensitive substring match on title
            results_objs = session.query(Listing).filter(Listing.title.ilike(f"%{q}%")).all()
            results = [
                {
                    "id": r.id,
                    "title": r.title,
                    "city": r.city,
                    "cost_per_month": r.cost_per_month
                } for r in results_objs
            ]
        finally:
            session.close()
    return templates.TemplateResponse(
        "search_page.html",
        {"request": request, "query": q or "", "results": results, "map_key": map_key}
    )

@app.get("/profile/{user_id}", response_class=HTMLResponse)
def show_profile(request: Request, user_id: int):
    """
    Render a user's profile page by id and include that user's listings.
    """
    session = SessionLocal()
    try:
        user_obj = session.get(User, user_id)
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")

        # convert user to a plain dict to avoid ORM lazy-loading after session close
        user_data = {
            "id": user_obj.id,
            "name": user_obj.name,
            "email": user_obj.email,
        }

        # load listings for this user
        listings_objs = session.query(Listing).filter(Listing.lister == user_id).all()
        listings_data = [
            {
                "id": l.id,
                "title": l.title,
                "city": l.city,
                "cost_per_month": l.cost_per_month
            } for l in listings_objs
        ]
    finally:
        session.close()

    return templates.TemplateResponse("profile.html", {"request": request, "user": user_data, "listings": listings_data})