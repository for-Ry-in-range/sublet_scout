from pydantic import BaseModel
from datatime import date

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