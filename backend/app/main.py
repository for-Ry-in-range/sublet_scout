from dotenv import load_dotenv
load_dotenv()

from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os, bcrypt

from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.routes.listing import router as listing_router
from app.routes.booking_request import router as booking_request_router
from app.models.listing import Listing
from app.schemas import SearchFilterStructure  # FIX: add this

# Create tables (uses DATABASE_URL from .env)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(listing_router)
app.include_router(booking_request_router)

# Sessions (cookie-based)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change-me"), same_site="lax")

# Templates (point to frontend/html)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
FRONTEND_HTML = os.path.join(BASE_DIR, "..", "frontend", "html")
templates = Jinja2Templates(directory=FRONTEND_HTML)

# Mount static files so url_for('static', path='homepage.css') works
STATIC_DIR = os.path.join(BASE_DIR, "..", "frontend", "css")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def is_edu(email: str) -> bool:
    return isinstance(email, str) and email.strip().lower().endswith(".edu")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

@app.get("/health")
def health():
    return {"ok": True}

# Serve login page
@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    # If session exists, go to profile instead of showing login
    if request.session.get("user_id"):
        return RedirectResponse(url="/profile", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

# Sign up (.edu only) -> create user
@app.post("/signup")
def signup(
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(""),
    last_name: str = Form(""),
):
    if not is_edu(email):
        raise HTTPException(status_code=400, detail="Email must end with .edu")
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            return JSONResponse({"ok": True, "message": "Account already exists. Please log in."})
        name = " ".join([x for x in [first_name.strip(), last_name.strip()] if x]).strip()
        user = User(name=name, email=email, password_hash=hash_password(password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return JSONResponse({"ok": True, "message": "Account created. You can now log in."})
    finally:
        db.close()

# Login -> set session and redirect
@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    if not is_edu(email):
        raise HTTPException(status_code=400, detail="Email must end with .edu")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not check_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        request.session["user_id"] = user.id
        return JSONResponse({"ok": True, "message": "Logged in", "redirect": "/profile"})
    finally:
        db.close()

# Profile (requires session)
@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        return RedirectResponse(url="/login", status_code=303)
    db = SessionLocal()
    try:
        try:
            user = db.get(User, uid)          # SQLAlchemy 2.x
        except Exception:
            user = db.query(User).get(uid)     # SQLAlchemy 1.x fallback
        if not user:
            request.session.clear()
            return RedirectResponse(url="/login", status_code=303)
        listings = db.query(Listing).filter(Listing.lister == uid).all()
        return templates.TemplateResponse("profile.html", {"request": request, "user": user, "listings": listings, "user_id": uid})
    finally:
        db.close()

# Render create listing form (session required)
@app.get("/create_listing", response_class=HTMLResponse)
def render_create_listing(request: Request):
    if not request.session.get("user_id"):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("create_listing.html", {"request": request})
 
@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/users")
def list_users():
    session = SessionLocal()
    users = session.query(User).all()
    result = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
    session.close()
    return result

@app.get("/homepage", response_class=HTMLResponse)
def show_homepage(
    request: Request,
    q: str | None = None,
    price: float | None = None,
    dates: str | None = None,
    user_id: int | None = None
):
    map_key = os.getenv("GOOGLE_MAP_KEY")
    user_name = None
    listings_data = []

    session = SessionLocal()
    try:
        if user_id is not None:
            user_obj = session.get(User, user_id)
            if user_obj:
                user_name = user_obj.name

        # Build query (simple filters for q and price)
        query_stmt = session.query(Listing)
        if q:
            q_like = f"%{q}%"
            query_stmt = query_stmt.filter(
                (Listing.title.ilike(q_like)) |
                (Listing.city.ilike(q_like)) |
                (Listing.address.ilike(q_like))
            )
        if price:
            query_stmt = query_stmt.filter(Listing.cost_per_month <= price)

        results = query_stmt.all()
        for l in results:
            full_address = ", ".join(filter(None, [l.address, l.city, l.state, l.zip_code]))
            listings_data.append({
                "id": l.id,
                "title": l.title,
                "address": l.address,
                "city": l.city,
                "state": l.state,
                "zip_code": l.zip_code,
                "full_address": full_address,
                "cost_per_month": l.cost_per_month or 0,
                "latitude": l.latitude,
                "longitude": l.longitude
            })
    finally:
        session.close()

    return templates.TemplateResponse(
        "homepage.html",
        {
            "request": request,
            "listings": listings_data,
            "map_key": map_key,
            "user_name": user_name,
            "user_id": user_id,
            "query": q or "",
            "price": price or "",
            "dates": dates or ""
        }
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

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user_data, "listings": listings_data, "user_id": user_id, "user_name": user_data["name"]}
    )

@app.get("/search_results")
def get_search_results(filters: SearchFilterStructure):
    session = SessionLocal()
    try:
        query = session.query(Listing)  # Initialize query for the Listing table
        if filters.cost_per_month is not None:
            query = query.filter(Listing.cost_per_month <= filters.cost_per_month)
        if filters.bedrooms_available is not None:
            query = query.filter(Listing.bedrooms_available >= filters.bedrooms_available)
        if filters.bathrooms is not None:
            query = query.filter(Listing.bathrooms >= filters.bathrooms)
        if filters.available_start_date is not None:
            query = query.filter(Listing.available_start_date <= filters.available_start_date)
        if filters.available_end_date is not None:
            query = query.filter(Listing.available_end_date >= filters.available_end_date)
        results = query.all()
        return results
    finally:
        session.close()

# Map page (renders Google Maps)
@app.get("/map", response_class=HTMLResponse)
def map_page(request: Request):
    return templates.TemplateResponse(
        "map.html",
        {"request": request, "google_maps_key": os.getenv("GOOGLE_MAP_KEY", "")},
    )

# Listings for map (only those with coordinates)
@app.get("/api/listings")
def api_listings():
    db = SessionLocal()
    try:
        rows = (
            db.query(Listing)
            .filter(Listing.latitude.isnot(None), Listing.longitude.isnot(None))
            .all()
        )
        def to_dict(l):
            return {
                "id": l.id,
                "title": l.title,
                "bedrooms_available": l.bedrooms_available,
                "total_rooms": l.total_rooms,
                "bedrooms_in_use": l.bedrooms_in_use,
                "bathrooms": l.bathrooms,
                "cost_per_month": float(l.cost_per_month) if getattr(l, "cost_per_month", None) is not None else None,
                "available_start_date": str(l.available_start_date) if getattr(l, "available_start_date", None) is not None else None,
                "available_end_date": str(l.available_end_date) if getattr(l, "available_end_date", None) is not None else None,
                "address": l.address,
                "city": l.city,
                "state": l.state,
                "zip_code": l.zip_code,
                "amenities": l.amenities,
                "latitude": float(l.latitude) if l.latitude is not None else None,
                "longitude": float(l.longitude) if l.longitude is not None else None,
                "image1": l.image1,
                "image2": l.image2,
                "image3": l.image3,
                "image4": l.image4,
            }
        return {"items": [to_dict(l) for l in rows]}
    finally:
        db.close()

