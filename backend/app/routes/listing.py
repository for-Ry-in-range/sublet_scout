from fastapi import APIRouter, Depends
from app.database import get_db
from app.crud.listing_crud import *
from app.schemas import ListingStructure

router = APIRouter()

@router.get("/listings/{listing_id}")
def read_listing(listing_id: int, db=Depends(get_db)):
    listing = get_listing_by_id(db, listing_id)
    return listing

@router.post("/listings/add")
def create_listing(listing_data: ListingStructure, db=Depends(get_db)):
    return create_listing(db, listing_data)

@router.delete("/listings/del/{listing_id}")
def delete_listing(listing_id: int, db=Depends(get_db)):
    return delete_listing(db, listing_id)