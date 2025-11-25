from fastapi import FastAPI, Request, HTTPException, status, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import hashlib, hmac, binascii, os, requests
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.listing import Listing
from app.schemas import SearchFilterStructure
from app.routes.listing import router as listing_router
from app.routes.booking_request import router as br_router
from pydantic import BaseModel, EmailStr
from itsdangerous import BadSignature, SignatureExpired
import bcrypt
from app.supabase_client import supabase
from app.email_verification import (
    hash_password, make_verification_link, send_verification_email, serializer
)

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
@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

def is_edu(email: str) -> bool:
    return isinstance(email, str) and email.lower().endswith(".edu")

class SignupPayload(BaseModel):
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None

@app.post("/signup")
async def signup(payload: SignupPayload):
    if not is_edu(payload.email):
        raise HTTPException(status_code=400, detail="Email must end with .edu")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # If already verified/user exists -> generic success
    existing = supabase.table("users").select("id").eq("email", payload.email).limit(1).execute()
    if existing.data:
        return {"ok": True, "message": "If the account exists, a verification email has been sent."}

    name = " ".join(filter(None, [payload.first_name, payload.last_name])) or None
    pwd_hash = hash_password(payload.password)
    verify_url = make_verification_link(payload.email, name, pwd_hash)

    try:
        send_verification_email(payload.email, verify_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to send verification email: {e}")

    return {"ok": True, "message": "Check your email for a verification link."}

@app.get("/verify", response_class=HTMLResponse)
async def verify(token: str):
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24)
        email = data["email"]
        name = data.get("name") or ""
        password_hash = data["password_hash"]
    except SignatureExpired:
        raise HTTPException(status_code=400, detail="Verification link expired")
    except BadSignature:
        raise HTTPException(status_code=400, detail="Invalid verification link")

    exists = supabase.table("users").select("id").eq("email", email).limit(1).execute()
    if not exists.data:
        supabase.table("users").insert({
            "name": name,
            "email": email,
            "password_hash": password_hash
        }).execute()

    return HTMLResponse("""
    <html><body style="font-family:system-ui">
      <h2>Email verified</h2>
      <p>Your account has been created. You can now <a href="/">log in</a>.</p>
    </body></html>
    """)

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...)):
    if not is_edu(email):
        raise HTTPException(status_code=400, detail="Email must end with .edu")

    resp = supabase.table("users").select("id,password_hash").eq("email", email).limit(1).execute()
    if not resp.data:
        raise HTTPException(status_code=401, detail="Invalid credentials or email not verified")

    row = resp.data[0]
    if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return JSONResponse({"ok": True, "message": "Logged in"})

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

@app.get("/create_listing", response_class=HTMLResponse)
def render_create_listing(request: Request, user_id: int):
    return templates.TemplateResponse(
        "create_listing.html",
        {"request": request, "user_id": user_id}
    )

@app.post("/create_listing")
def create_listing(
    request: Request,
    user_id: int = Form(...),
    title: str = Form(...),
    bedrooms_available: int = Form(...),
    total_rooms: int = Form(...),
    bedrooms_in_use: int = Form(...),
    bathrooms: int = Form(...),
    cost_per_month: float = Form(...),
    available_start_date: str = Form(...),
    available_end_date: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    amenities: str = Form(""),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
):
    session = SessionLocal()
    try:
        # Basic validation
        if cost_per_month < 0:
            raise HTTPException(status_code=400, detail="Invalid price")

        listing = Listing(
            title=title,
            lister=user_id,
            bedrooms_available=bedrooms_available,
            total_rooms=total_rooms,
            bedrooms_in_use=bedrooms_in_use,
            bathrooms=bathrooms,
            cost_per_month=cost_per_month,
            available_start_date=available_start_date,
            available_end_date=available_end_date,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            amenities=amenities,
            latitude=latitude,
            longitude=longitude,
        )
        session.add(listing)
        session.commit()
        session.refresh(listing)
    finally:
        session.close()

    return RedirectResponse(url=f"/profile/{user_id}", status_code=303)

