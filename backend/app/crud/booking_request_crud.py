from sqlalchemy.orm import Session
from app.models.apartment import Apartment

def get_booking_request_by_id(db: Session, booking_request_id: int):


def create_booking_request(db: Session, json_data: dict):


def delete_booking_request(db: Session, booking_request_id: int):
    