from sqlalchemy.orm import Session
from app.models.booking_request import BookingRequest
from app.schemas import BookingRequestStructure

def get_booking_request_by_id(db: Session, booking_request_id: int):
    br_data = db.query(BookingRequest).filter(BookingRequest.id == booking_request_id).first()
    if not br_data:
        return None
    return {
        "listing_id": br_data.listing_id,
        "subletter_id": br_data.subletter_id,
    }

def create_booking_request(db: Session, br_data: dict):
    new_br = BookingRequest(
        listing_id=br_data.listing_id,
        subletter_id=br_data.subletter_id,
    )
    db.add(new_br)
    db.commit()
    db.refresh(new_br)
    return new_br

def delete_booking_request(db: Session, br_id: int):
    br = db.query(BookingRequest).filter(BookingRequest.id == br_id).first()
    if not br:
        return None
    db.delete(br)
    db.commit()
    return {"message": "Deleted booking request with ID:": br_id}