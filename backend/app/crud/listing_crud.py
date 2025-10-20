from sqlalchemy.orm import Session
from app.models.listing import Listing
from app.schemas import ListingStructure

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

def create_listing(db: Session, listing_data: ListingStructure):
    new_listing = Listing(
        title=listing_data.title,
        lister=listing_data.lister,
        bedrooms_available=listing_data.bedrooms_available,
        total_rooms=listing_data.total_rooms,
        bedrooms_in_use=listing_data.bedrooms_in_use,
        bathrooms=listing_data.bathrooms,
        cost_per_month=listing_data.cost_per_month,
        available_start_date=listing_data.available_start_date,
        available_end_date=listing_data.available_end_date,
        address=listing_data.address,
        city=listing_data.city,
        state=listing_data.state,
        zip_code=listing_data.zip_code,
        amenities=listing_data.amenities,
    )
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)
    return new_listing


def delete_listing(db: Session, listing_id: int):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return None
    db.delete(listing)
    db.commit()
    return {"message": "Deleted listing with ID:": listing_id}