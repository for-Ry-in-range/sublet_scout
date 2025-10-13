from fastapi import APIRouter, Depends
from app.database import get_db
from app.crud.apartment_crud import get_apartment_by_id

router = APIRouter()

@router.get("/apartments/{apartment_id}")
def read_apartment(apartment_id: int, db=Depends(get_db)):
    apartment = get_apartment_by_id(db, apartment_id)
    return apartment