from fastapi import APIRouter, Depends
from app.database import get_db
from app.crud.booking_request_crud import *
from app.schemas import *

router = APIRouter()

@router.get("/booking_request/{booking_request_id}")
def read_booking_request_endpoint(booking_request_id: int, db=Depends(get_db)):
    try:
        res = get_booking_request_by_id(db, booking_request_id)
        if not res:
            raise HTTPException(status_code=404, detail="Booking request not found")
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_booking_request")
def create_booking_request_endpoint(request_data: BookingRequestStructure, db=Depends(get_db)):
    try:
        res = create_booking_request(db, request_data)
        return {"message": "Booking request created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_booking_request/{booking_request_id}")
def delete_booking_request_endpoint(booking_request_id: int, db=Depends(get_db)):
    try:
        res = delete_booking_request(db, booking_request_id)
        if not res:
            raise HTTPException(status_code=404, detail="Booking request not found")
        return { "message": "Booking request deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))