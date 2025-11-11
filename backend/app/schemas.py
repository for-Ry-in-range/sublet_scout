from pydantic import BaseModel
from datetime import date

class ListingStructure(BaseModel):
    title: str
    lister: int
    bedrooms_available: int
    total_rooms: int
    bedrooms_in_use: int
    bathrooms: int
    cost_per_month: float
    available_start_date: date
    available_end_date: date
    address: str
    city: str
    state: str
    zip_code: str
    amenities: str

class BookingRequestStructure(BaseModel):
    listing_id: int
    subletter_id: int

class SearchFilterStructure(BaseModel):
    cost_per_month: float
    bedrooms_available: int
    bathrooms: int
    available_start_date: date
    available_end_date: date