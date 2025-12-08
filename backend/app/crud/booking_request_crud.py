from sqlalchemy.orm import Session
from app.models.booking_request import BookingRequest
from app.models.listing import Listing
from app.models.user import User
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

        
def create_booking_request(data):
    db = SessionLocal()
    try:
        # prevent duplicates
        existing = db.query(BookingRequest).filter(
            BookingRequest.subletter_id == data.subletter_id,
            BookingRequest.listing_id == data.listing_id
        ).first()
        if existing:
            return {"error": "Request already exists"}

        new = BookingRequest(
            listing_id=data.listing_id,
            subletter_id=data.subletter_id,
        )
        db.add(new)
        db.commit()
        db.refresh(new)
        return new
    finally:
        db.close()


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

def get_incoming_requests(owner_id: int):
    session = SessionLocal()
    try:
        rows = (
            session.query(BookingRequest, Listing, User)
            .join(Listing, BookingRequest.listing_id == Listing.id)
            .join(User, BookingRequest.subletter_id == User.id)
            .filter(Listing.lister == owner_id, BookingRequest.status == "pending")
            .all()
        )

        out = []
        for req, listing, user in rows:
            req_dict = {
                "id": req.id,
                "listing_id": req.listing_id,
                "subletter_id": req.subletter_id,
                "status": req.status,
                "created_at": req.created_at.isoformat() if getattr(req, "created_at", None) else None,
            }
            listing_dict = {
                "id": listing.id,
                "title": listing.title,
                "city": listing.city,
                "cost_per_month": float(listing.cost_per_month) if listing.cost_per_month is not None else None,
            }
            user_dict = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            }
            out.append([req_dict, listing_dict, user_dict])

        return out
    finally:
        session.close()

def approve_request(req_id, owner_id):
    db = SessionLocal()
    try:
        req = db.query(BookingRequest).filter(BookingRequest.id == req_id).first()
        if not req:
            return {"error": "Request not found"}

        listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
        if listing.lister != owner_id:
            return {"error": "Unauthorized"}

        req.status = "approved"
        db.commit()

        requester = db.query(User).filter(User.id == req.subletter_id).first()
        owner = db.query(User).filter(User.id == owner_id).first()

        return {
            "ok": True,
            "contact_info": {
                "owner_email": owner.email,
                "requester_email": requester.email
            }
        }
    finally:
        db.close()

def reject_request(req_id, owner_id):
    db = SessionLocal()
    try:
        req = db.query(BookingRequest).filter(BookingRequest.id == req_id).first()
        if not req:
            return {"error": "Request not found"}

        listing = db.query(Listing).filter(Listing.id == req.listing_id).first()
        if listing.lister != owner_id:
            return {"error": "Unauthorized"}

        req.status = "rejected"
        db.commit()
        return {"ok": True}
    finally:
        db.close()