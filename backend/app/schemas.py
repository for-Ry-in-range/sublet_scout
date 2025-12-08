from pydantic import BaseModel
from datetime import date
from typing import Optional

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
    image1: str
    image2: str
    image3: str
    image4: str

class BookingRequestStructure(BaseModel):
    listing_id: int
    subletter_id: int

class SearchFilterStructure(BaseModel):
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None