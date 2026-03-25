"""
routers/listings.py — All API endpoints for property listings

A "router" is a group of related endpoints.
This file handles everything to do with listings:
  GET    /listings                  → return all listings
  GET    /listings/{id}             → return one listing
  POST   /listings                  → create a new listing (admin only)
  PUT    /listings/{id}             → edit a listing (admin only)
  DELETE /listings/{id}             → delete a listing (admin only)
  POST   /listings/{id}/upload-image → upload a photo for a listing (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os, cloudinary, cloudinary.uploader

import models
import schemas
from database import get_db
from routers.deps import get_current_admin  # Our auth dependency

# Configure Cloudinary from environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# APIRouter groups these endpoints together
# The prefix means every route here starts with /listings
router = APIRouter(prefix="/listings", tags=["Listings"])


@router.get("/", response_model=List[schemas.ListingResponse])
def get_all_listings(
    location:     str   = None,  # Optional filter: ?location=Phnom Penh
    max_price:    float = None,  # Optional filter: ?max_price=300000
    listing_type: str   = None,  # Optional filter: ?listing_type=rent
    db: Session = Depends(get_db)
):
    """
    Return all listings.
    Optionally filter by location, max price, and/or listing type.
    Example: GET /listings?location=Siem Reap&listing_type=rent
    """
    query = db.query(models.Listing)

    if location:
        query = query.filter(models.Listing.location == location)

    if max_price:
        query = query.filter(models.Listing.price <= max_price)

    if listing_type:
        query = query.filter(models.Listing.listing_type == listing_type)

    return query.all()


@router.get("/{listing_id}", response_model=schemas.ListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """
    Return one listing by its ID.
    Example: GET /listings/3
    """
    listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()

    if not listing:
        # 404 means "not found"
        raise HTTPException(status_code=404, detail="Listing not found")

    return listing


@router.post("/", response_model=schemas.ListingResponse, status_code=201)
def create_listing(
    data: schemas.ListingCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # 🔒 Admin only — must have valid token
):
    """
    Create a new listing. Admin only.
    Expects a JSON body matching the ListingCreate schema.
    Returns the created listing with its new ID.
    """
    new_listing = models.Listing(**data.model_dump())  # Convert schema to DB model
    db.add(new_listing)
    db.commit()
    db.refresh(new_listing)  # Reload from DB to get auto-generated fields (id, created_at)
    return new_listing


@router.put("/{listing_id}", response_model=schemas.ListingResponse)
def update_listing(
    listing_id: int,
    data: schemas.ListingUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # 🔒 Admin only
):
    """
    Edit an existing listing. Admin only.
    Only updates fields that are provided — leave others unchanged.
    """
    listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Only update fields that were actually sent (not None)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(listing, field, value)

    db.commit()
    db.refresh(listing)
    return listing


@router.delete("/{listing_id}", status_code=204)
def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # 🔒 Admin only
):
    """
    Delete a listing by ID. Admin only.
    Returns 204 (No Content) on success.
    """
    listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    db.delete(listing)
    db.commit()
    # 204 means success but no data to return


# Only allow these file types — prevents uploading dangerous files
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


@router.post("/{listing_id}/upload-image", response_model=schemas.ListingResponse)
async def upload_image(
    listing_id: int,
    file: UploadFile = File(...),   # File(...) means this field is required
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # 🔒 Admin only
):
    """
    Upload a photo for a listing. Admin only.

    How it works:
      1. Validate the file type and size
      2. Upload to Cloudinary using the listing ID as the public_id
         (overwrite=True means re-uploading automatically replaces the old image)
      3. Save the returned Cloudinary URL to the listing
      4. Return the updated listing

    Images are stored permanently on Cloudinary — they survive server restarts
    and redeploys unlike local disk storage.
    """
    listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only JPEG, PNG, and WebP are allowed."
        )

    # Read the file content and check its size
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    # Upload to Cloudinary
    # public_id uses the listing ID so each listing has one image slot on Cloudinary.
    # overwrite=True means uploading a new image automatically replaces the old one.
    result = cloudinary.uploader.upload(
        content,
        public_id=f"nestkh/listing_{listing_id}",
        overwrite=True,
        resource_type="image"
    )

    # Cloudinary returns a permanent HTTPS URL — save it to the database
    listing.image_url = result["secure_url"]
    db.commit()
    db.refresh(listing)

    return listing
