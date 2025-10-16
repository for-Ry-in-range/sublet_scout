from sqlalchemy.orm import Session
from app.models.apartment import Apartment

def get_apartment_by_id(db: Session, apartment_id: int):


def create_listing(db: Session, json_data: dict):


def update_listing(db: Session, apartment_id: int, json_data: dict):


def delete_listing(db: Session, apartment_id: int):
    