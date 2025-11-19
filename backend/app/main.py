from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import hashlib, hmac, binascii, os
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.listing import Listing
from app.schemas import SearchFilterStructure
from app.routes.listing import router as listing_router
from app.routes.booking_request import router as br_router
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

app.include_router(listing_router)
app.include_router(br_router)

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

def hash_password(password: str, iterations: int = 100_000) -> str:
    """Return a string storing iterations, salt, and hash so we can verify later."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{iterations}${binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

import hmac  # add this at the top

def verify_password(stored: str, password: str) -> bool:
    """Verify password against stored string created by hash_password."""
    try:
        iterations_str, salt_hex, hash_hex = stored.split("$")
        iterations = int(iterations_str)
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


@app.post("/signup")
async def signup(request: Request):
    """
    Accepts JSON { email, password } and creates a user if:
      - email ends with .edu
      - password length >= 8
      - email unique
    Returns JSON 201 on success or a JSON error message.
    """
    data = {}
    # Accept JSON body (frontend signup uses fetch JSON)
    try:
        data = await request.json()
    except Exception:
        # Not a JSON body
        return JSONResponse({"message": "Expected JSON body"}, status_code=status.HTTP_400_BAD_REQUEST)

    email = (data.get("email") or "").strip().lower()
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    password = data.get("password") or ""

    if not email.endswith(".edu"):
        return JSONResponse({"message": "Email must end with .edu"}, status_code=status.HTTP_400_BAD_REQUEST)
    if not first_name:
        return JSONResponse({"message": "First name is required"}, status_code=status.HTTP_400_BAD_REQUEST)
    if not last_name:
        return JSONResponse({"message": "Last name is required"}, status_code=status.HTTP_400_BAD_REQUEST)
    if len(password) < 8:
        return JSONResponse({"message": "Password must be at least 8 characters"}, status_code=status.HTTP_400_BAD_REQUEST)

    full_name = f"{first_name} {last_name}"

    session = SessionLocal()
    try:
        # Check uniqueness
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            return JSONResponse({"message": "Email already registered"}, status_code=status.HTTP_409_CONFLICT)

        # Hash password
        password_hash = hash_password(password)

        new_user = User(name=full_name, email=email, password_hash=password_hash)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

        return JSONResponse({"message": "Account created", "user": {"id": new_user.id, "email": new_user.email}}, status_code=status.HTTP_201_CREATED)
    finally:
        session.close()

@app.post("/login")
async def login(request: Request):
    """
    Accepts form POST (from your current login form) or JSON {email, password}.
    On successful auth, redirects to /homepage. On failure returns 401 JSON or a simple message.
    """
    # Try JSON first
    email = password = None
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            email = (body.get("email") or "").strip().lower()
            password = body.get("password") or ""
        except Exception:
            return JSONResponse({"message": "Invalid JSON"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        # fallback to form data (your login form submits form POST)
        form = await request.form()
        email = (form.get("email") or "").strip().lower()
        password = form.get("password") or ""


    if not email or not password:
        return JSONResponse({"message": "Email and password required"}, status_code=status.HTTP_400_BAD_REQUEST)

    session = SessionLocal()
    try:
        user_obj = session.query(User).filter(User.email == email).first()
        if not user_obj:
            # keep response generic in real apps; for dev we return message
            return JSONResponse({"message": "User doesn't exist"}, status_code=status.HTTP_401_UNAUTHORIZED)

        if not verify_password(user_obj.password_hash, password):
            return JSONResponse({"message": "Incorrect password"}, status_code=status.HTTP_401_UNAUTHORIZED)

        # Auth succeeded. For now we simply redirect to homepage.
        # NOTE: no session/cookie is set — add session or JWT later if you want persistent login.
        return RedirectResponse(url=f"/homepage?user_id={user_obj.id}", status_code=status.HTTP_303_SEE_OTHER)
    finally:
        session.close()


@app.get("/homepage", response_class=HTMLResponse)
def show_homepage(request: Request, q: str | None = None, price: int | None = None, dates: str | None = None, user_id: int | None = None):
    map_key = os.getenv("GOOGLE_MAP_KEY")
    results = []
    user_name = None
    session = SessionLocal()
    try:
        # load user name for nav if user_id provided
        if user_id is not None:
            user_obj = session.get(User, user_id)
            if user_obj:
                user_name = user_obj.name

        # Always load some listings for the page (e.g., for future use)
        listings = session.query(Listing).all()
        listings_data = [
            {
                "id": l.id,
                "title": l.title,
                "city": l.city,
                "cost_per_month": l.cost_per_month
            } for l in listings
        ]

        # If a query or filters were provided, run a filtered search
        if q or price or dates:
            query = session.query(Listing)
            if q:
                q_like = f"%{q}%"
                query = query.filter((Listing.title.ilike(q_like)) | (Listing.city.ilike(q_like)))
            if price:
                query = query.filter(Listing.cost_per_month <= price)
            # dates parsing/logic may be implemented later; for now we ignore 'dates' or you can add date filters later
            results_objs = query.all()
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
        "homepage.html",
        {
            "request": request,
            "listings": listings_data,
            "results": results,
            "map_key": map_key,
            "user_name": user_name,
            "user_id": user_id,
            "query": q or ""
        }
    )

@app.get("/individual_apt", response_class=HTMLResponse)
async def render_individual_apt(request: Request, user_id: int | None = None):
    map_key = os.getenv("GOOGLE_MAP_KEY")
    user_name = None
    if user_id is not None:
        session = SessionLocal()
        try:
            user_obj = session.get(User, user_id)
            if user_obj:
                user_name = user_obj.name
        finally:
            session.close()

    return templates.TemplateResponse("individual_apt.html", {"request": request, "map_key": map_key, "user_id": user_id, "user_name": user_name})

# deprecate later
@app.get("/search", response_class=HTMLResponse)
def show_search(q: str | None = None, user_id: int | None = None):
    redirect_url = "/homepage"
    params = []
    if q:
        params.append(f"q={q}")
    if user_id is not None:
        params.append(f"user_id={user_id}")
    if params:
        redirect_url = f"{redirect_url}?{'&'.join(params)}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

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

@app.get("/search_results")
def get_search_results(filters: SearchFilterStructure):
    session = SessionLocal()
    try:
        query = session.query(Listing)  # Initialize query for the Listing table
        if filters.cost_per_month:
            query = query.filter(Listing.cost_per_month <= filters.cost_per_month)
        if filters.bedrooms_available:
            query = query.filter(Listing.bedrooms_available >= filters.bedrooms_available)
        if filters.bathrooms:
            query = query.filter(Listing.bathrooms >= filters.bathrooms)
        if filters.available_start_date:
            query = query.filter(Listing.available_start_date <= filters.available_start_date)
        if filters.available_end_date:
            query = query.filter(Listing.available_end_date >= filters.available_end_date)
        results = query.all()
        return results
    finally:
        session.close()