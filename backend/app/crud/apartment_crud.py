from sqlalchemy.orm import Session
from app.models.apartment import Apartment

def get_apartment_by_id(db: Session, apartment_id: int):
    
