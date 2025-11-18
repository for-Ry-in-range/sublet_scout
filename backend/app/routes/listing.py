from fastapi import APIRouter, Depends
from app.database import get_db
from app.crud.listing_crud import *
from app.schemas import ListingStructure

router = APIRouter()

@router.get("/listings/{listing_id}")
def read_listing_endpoint(listing_id: int):
    return get_listing_by_id(listing_id)

@router.post("/listings/add")
def create_listing_endpoint(listing_data: ListingStructure):
    return create_listing(listing_data)

@router.delete("/listings/del/{listing_id}")
def delete_listing_endpoint(listing_id: int):
    return delete_listing(listing_id)