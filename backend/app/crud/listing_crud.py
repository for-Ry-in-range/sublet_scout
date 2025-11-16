from sqlalchemy.orm import Session
from app.models.listing import Listing
from app.schemas import ListingStructure
from app.database import SessionLocal

def get_listing_by_id(db: Session, listing_id: int):
    listing_data = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing_data:
        return None
    return {
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
    }

def create_listing(listing_data: ListingStructure):
    session = SessionLocal()
    try:
        new_listing = Listing(title=listing_data.title, lister=listing_data.lister, bedrooms_available=listing_data.bedrooms_available, total_rooms=listing_data.total_rooms, bedrooms_in_use=listing_data.bedrooms_in_use, bathrooms=listing_data.bathrooms, cost_per_month=listing_data.cost_per_month, available_start_date=listing_data.available_start_date, available_end_date=listing_data.available_end_date, address=listing_data.address, city=listing_data.city, state=listing_data.state, zip_code=listing_data.zip_code, amenities=listing_data.amenities)
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