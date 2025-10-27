from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from app.database import Base

class BookingRequest(Base):
    __tablename__ = "booking_requests"
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, ForeignKey("listings.id"))
    subletter_id = Column(Integer, ForeignKey("users.id"))