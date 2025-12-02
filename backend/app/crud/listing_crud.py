from sqlalchemy.orm import Session
from app.models.listing import Listing
from app.schemas import ListingStructure
from app.database import SessionLocal
from fastapi import status, Request, Form, UploadFile, File
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import os, requests
from fastapi.templating import Jinja2Templates
import base64

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "../..", "frontend")
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "html"))
 
async def image_to_base64(upload_file):
    file_bytes = await upload_file.read()
    base64_string = base64.b64encode(file_bytes).decode('utf-8')
    return base64_string

def get_listing_by_id(request: Request, listing_id: int, user_id: int | None = None):
    session = SessionLocal()
    try:
        # TODO: implement images later
        images = []
        
        query = session.query(Listing)
        listing_data = query.filter(Listing.id == listing_id).first()
        if not listing_data:
            return None
        apt = {
            "title": listing_data.title,
            "lister": listing_data.lister, 
            "bedrooms_available": listing_data.bedrooms_available,
            "total_rooms": listing_data.total_rooms,
            "bedrooms_in_use": listing_data.bedrooms_in_use, 
            "bathrooms": listing_data.bathrooms,
            "cost_per_month": listing_data.cost_per_month,
            "available_start_date": listing_data.available_start_date,
            "available_end_date": listing_data.available_end_date,
            "address": listing_data.address,
            "city": listing_data.city,
            "state": listing_data.state,
            "zip_code": listing_data.zip_code,
            "amenities": listing_data.amenities,
            "image1": listing_data.image1,
            "image2": listing_data.image2,
            "image3": listing_data.image3,
            "image4": listing_data.image4,
        }
        # Get name for navbar
        user_name = None
        if user_id:
            user = session.get(User, user_id)
            if user:
                user_name = user.name

    finally:
        session.close()

    map_key = os.getenv("GOOGLE_MAP_KEY")

    return templates.TemplateResponse(
        "individual_apt.html",
        {
            "request": request,
            "apt": apt,
            "map_key": map_key,
            "user_id": user_id,
            "user_name": user_name
        }
    )
    

async def create_listing(
    request: Request,
    title: str,
    bedrooms_available: int,
    total_rooms: int,
    bedrooms_in_use: int,
    bathrooms: int,
    cost_per_month: float,
    available_start_date: str,
    available_end_date: str,
    address: str,
    city: str,
    state: str,
    zip_code: str,
    amenities: str,
    image1: UploadFile = None,
    image2: UploadFile = None,
    image3: UploadFile = None,
    image4: UploadFile = None,
):

    # Getting longitude and latitude

    map_key = os.getenv("GOOGLE_MAP_KEY")
    full_address = f"{address}, {city}, {state} {zip_code}"

    geo_url = (
        "https://maps.googleapis.com/maps/api/geocode/json"
        f"?address={full_address}&key={map_key}"
    )

    geo_response = requests.get(geo_url).json()

    if geo_response["status"] != "OK":
        raise HTTPException(status_code=400, detail="Invalid address - could not geocode")

    location = geo_response["results"][0]["geometry"]["location"]
    latitude = location["lat"]
    longitude = location["lng"]

    # Convert images to base64
    image1_base64 = await image_to_base64(image1)
    image2_base64 = await image_to_base64(image2)
    image3_base64 = await image_to_base64(image3)
    image4_base64 = await image_to_base64(image4)

    # Adding the listing to database

    uid = request.session.get("user_id")
    if not uid:
        return RedirectResponse(url="/login", status_code=303)
    session = SessionLocal()
    try:
        new_listing = Listing(title=title, lister=uid, bedrooms_available=bedrooms_available, total_rooms=total_rooms, bedrooms_in_use=bedrooms_in_use, bathrooms=bathrooms, cost_per_month=cost_per_month, available_start_date=available_start_date, available_end_date=available_end_date, address=address, city=city, state=state, zip_code=zip_code, amenities=amenities, latitude=latitude, longitude=longitude, image1=image1_base64, image2=image2_base64, image3=image3_base64, image4=image4_base64)
        session.add(new_listing)
        session.commit()
        session.refresh(new_listing) # Adds the id to new_listing
        return JSONResponse({"message": "Listing added", "listing": {"id": new_listing.id, "title": new_listing.title}}, status_code=status.HTTP_201_CREATED)
    finally:
        session.close()


def delete_listing(listing_id: int):
    session = SessionLocal()
    try:
        listing = session.query(Listing).filter(Listing.id == listing_id).first()
        if not listing:
            return JSONResponse(
                {"detail": f"Listing {listing_id} not found"},
                status_code=status.HTTP_404_NOT_FOUND
            )
        session.delete(listing)
        session.commit()
        return JSONResponse(
            {"message": "Deleted listing", "listing": listing_id},
            status_code=status.HTTP_200_OK
        )
    finally:
        session.close()