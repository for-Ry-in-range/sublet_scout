from fastapi import APIRouter, Depends, Request
from app.database import get_db
from app.crud.listing_crud import *
from app.schemas import ListingStructure

router = APIRouter()

@router.get("/listings/{listing_id}")
def read_listing_endpoint(request: Request, listing_id: int):
    return get_listing_by_id(request, listing_id, None)
 
@router.post("/listings")
async def create_listing_endpoint(
    request: Request,
    title: str = Form(...),
    bedrooms_available: int = Form(...),
    total_rooms: int = Form(...),
    bedrooms_in_use: int = Form(...),
    bathrooms: int = Form(...),
    cost_per_month: float = Form(...),
    available_start_date: str = Form(...),
    available_end_date: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip_code: str = Form(...),
    amenities: str = Form(""),
    image1: UploadFile = File(None),
    image2: UploadFile = File(None),
    image3: UploadFile = File(None),
    image4: UploadFile = File(None),
):
    response = await create_listing(request=request, title=title, bedrooms_available=bedrooms_available, total_rooms=total_rooms, bedrooms_in_use=bedrooms_in_use, bathrooms=bathrooms, cost_per_month=cost_per_month, available_start_date=available_start_date, available_end_date=available_end_date, address=address, city=city, state=state, zip_code=zip_code, amenities=amenities, image1=image1, image2=image2, image3=image3, image4=image4)
    return response

@router.delete("/listings/{listing_id}")
def delete_listing_endpoint(listing_id: int):
    return delete_listing(listing_id)