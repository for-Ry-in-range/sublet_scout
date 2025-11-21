from sqlalchemy.orm import Session
from app.models.listing import Listing
from app.schemas import ListingStructure
from app.database import SessionLocal
from fastapi import status, Request
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import os, requests
from fastapi.templating import Jinja2Templates

load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "../..", "frontend")
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "html"))

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
            "amenities": listing_data.amenities
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
    

def create_listing(listing_data: ListingStructure):

    # Getting longitude and latitude

    map_key = os.getenv("GOOGLE_MAP_KEY")
    full_address = f"{listing_data.address}, {listing_data.city}, {listing_data.state} {listing_data.zip_code}"

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

    # Adding the listing to database

    session = SessionLocal()
    try:
        new_listing = Listing(title=listing_data.title, lister=listing_data.lister, bedrooms_available=listing_data.bedrooms_available, total_rooms=listing_data.total_rooms, bedrooms_in_use=listing_data.bedrooms_in_use, bathrooms=listing_data.bathrooms, cost_per_month=listing_data.cost_per_month, available_start_date=listing_data.available_start_date, available_end_date=listing_data.available_end_date, address=listing_data.address, city=listing_data.city, state=listing_data.state, zip_code=listing_data.zip_code, amenities=listing_data.amenities, latitude=latitude, longitude=longitude)
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