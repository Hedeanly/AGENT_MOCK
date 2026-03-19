"""
routers/enquiries.py — Enquiry form endpoints

Handles:
  POST /enquiries        → submit an enquiry (any visitor)
  GET  /enquiries        → view all enquiries with listing title (admin only)
  GET  /enquiries/{id}   → view a single enquiry (admin only)
  DELETE /enquiries/{id} → delete an enquiry (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
from routers.deps import get_current_admin

router = APIRouter(prefix="/enquiries", tags=["Enquiries"])


@router.post("/", response_model=schemas.EnquiryResponse, status_code=201)
def submit_enquiry(data: schemas.EnquiryCreate, db: Session = Depends(get_db)):
    """
    Submit an enquiry for a property.
    Anyone visiting the site can do this — no login required.
    """
    # Check the listing actually exists before saving the enquiry
    listing = db.query(models.Listing).filter(models.Listing.id == data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    new_enquiry = models.Enquiry(**data.model_dump())
    db.add(new_enquiry)
    db.commit()
    db.refresh(new_enquiry)

    # Attach the listing title to the response so the frontend doesn't need a second request
    result = schemas.EnquiryResponse.model_validate(new_enquiry)
    result.listing_title = listing.title
    return result


@router.get("/", response_model=List[schemas.EnquiryResponse])
def get_all_enquiries(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # 🔒 Admin only
):
    """
    Return all enquiries with the property title included. Admin only.

    We do a JOIN here — instead of just fetching enquiries, we also
    grab the listing title in the same query so the frontend doesn't
    have to make a separate request for each enquiry.
    """
    # Join enquiries with listings to get the title in one query
    # Result rows are tuples: (Enquiry, title_or_None)
    rows = (
        db.query(models.Enquiry, models.Listing.title)
        .outerjoin(models.Listing, models.Enquiry.listing_id == models.Listing.id)
        .order_by(models.Enquiry.created_at.desc())
        .all()
    )

    # Build the response objects, attaching the listing title to each
    results = []
    for enquiry, listing_title in rows:
        item = schemas.EnquiryResponse.model_validate(enquiry)
        item.listing_title = listing_title  # e.g. "Modern Villa with Private Pool"
        results.append(item)

    return results


@router.get("/{enquiry_id}", response_model=schemas.EnquiryResponse)
def get_enquiry(
    enquiry_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # 🔒 Admin only
):
    """Return a single enquiry by ID, with listing title."""
    row = (
        db.query(models.Enquiry, models.Listing.title)
        .outerjoin(models.Listing, models.Enquiry.listing_id == models.Listing.id)
        .filter(models.Enquiry.id == enquiry_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    enquiry, listing_title = row
    result = schemas.EnquiryResponse.model_validate(enquiry)
    result.listing_title = listing_title
    return result


@router.delete("/{enquiry_id}", status_code=204)
def delete_enquiry(
    enquiry_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # 🔒 Admin only
):
    """
    Delete an enquiry. Admin only.
    Useful for clearing spam or handled enquiries.
    """
    enquiry = db.query(models.Enquiry).filter(models.Enquiry.id == enquiry_id).first()

    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    db.delete(enquiry)
    db.commit()
