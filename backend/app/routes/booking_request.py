from fastapi import APIRouter, Depends
from app.database import get_db
from app.crud.booking_request_crud import *
from app.schemas import *

router = APIRouter()

@router.get("/booking_request/{booking_request_id}")
def read_booking_request(booking_request_id: int, db=Depends(get_db)):
    return get_booking_request_by_id(db, booking_request_id)

@router.get("/create_booking_request}")
def create_booking_request(request_data: BookingRequestStructure, db=Depends(get_db)):
    create_booking_request(db, request_data)

@router.delete("/create_booking_request/del/{booking_request_id}")
def delete_booking_request(booking_request_id: int, db=Depends(get_db)):
    return delete_booking_request(db, booking_request_id)