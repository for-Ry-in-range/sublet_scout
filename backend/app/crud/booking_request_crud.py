from sqlalchemy.orm import Session
from app.models.booking_request import BookingRequest
from app.schemas import BookingRequestStructure
from app.database import SessionLocal
from fastapi import status
from fastapi.responses import JSONResponse

def get_booking_request_by_id(booking_request_id: int):
    session = SessionLocal()
    try:
        query = session.query(BookingRequest)
        br_data = query.filter(BookingRequest.id == booking_request_id).first()
        if not br_data:
            return None
        return {
        "listing_id": br_data.listing_id,
        "subletter_id": br_data.subletter_id,
    }
    finally:
        session.close()

        
def create_booking_request(br_data: BookingRequestStructure):
    session = SessionLocal()
    try:
        new_br = BookingRequest(
            listing_id=br_data.listing_id,
            subletter_id=br_data.subletter_id,
        )
        session.add(new_br)
        session.commit()
        session.refresh(new_br) # Adds the id to new_br
        return JSONResponse({"message": "Booking request added", "br": {"id": new_br.id}}, status_code=status.HTTP_201_CREATED)
    finally:
        session.close()


def delete_booking_request(br_id: int):
    session = SessionLocal()
    try:
        br = session.query(BookingRequest).filter(BookingRequest.id == br_id).first()
        if not br:
            return JSONResponse(
                {"detail": f"Booking request {br_id} not found"},
                status_code=status.HTTP_404_NOT_FOUND
            )
        session.delete(br)
        session.commit()
        return JSONResponse(
            {"message": "Deleted booking request", "br_id": br_id},
            status_code=status.HTTP_200_OK
        )
    finally:
        session.close()