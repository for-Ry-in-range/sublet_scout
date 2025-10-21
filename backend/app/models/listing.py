from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from app.database import Base

class Listing(Base):
    __tablename__ = "listings"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    lister = Column(Integer, ForeignKey("users.id"))
    bedrooms_available = Column(Integer)
    total_rooms = Column(Integer)
    bedrooms_in_use = Column(Integer)
    bathrooms = Column(Integer)
    cost_per_month = Column(Float)
    available_start_date = Column(Date)
    available_end_date = Column(Date)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)  # String just in case there's leading zeros
    amenities = Column(String)