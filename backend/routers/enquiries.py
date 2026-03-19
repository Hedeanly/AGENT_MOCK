"""
routers/enquiries.py — Enquiry form endpoints

Handles:
  POST /enquiries        → submit an enquiry (any visitor can do this)
  GET  /enquiries        → view all enquiries (admin only in Phase 2)
  GET  /enquiries/{id}   → view a single enquiry
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db

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
    return new_enquiry


@router.get("/", response_model=List[schemas.EnquiryResponse])
def get_all_enquiries(db: Session = Depends(get_db)):
    """
    Return all enquiries.
    Will be restricted to admin only in Phase 2.
    """
    return db.query(models.Enquiry).order_by(models.Enquiry.created_at.desc()).all()


@router.get("/{enquiry_id}", response_model=schemas.EnquiryResponse)
def get_enquiry(enquiry_id: int, db: Session = Depends(get_db)):
    """Return a single enquiry by ID"""
    enquiry = db.query(models.Enquiry).filter(models.Enquiry.id == enquiry_id).first()

    if not enquiry:
        raise HTTPException(status_code=404, detail="Enquiry not found")

    return enquiry
