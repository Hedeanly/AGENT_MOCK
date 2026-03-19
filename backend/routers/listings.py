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
import os, uuid, shutil

import models
import schemas
from database import get_db
from routers.deps import get_current_admin  # Our auth dependency

# APIRouter groups these endpoints together
# The prefix means every route here starts with /listings
router = APIRouter(prefix="/listings", tags=["Listings"])


@router.get("/", response_model=List[schemas.ListingResponse])
def get_all_listings(
    location: str = None,   # Optional filter: ?location=Phnom Penh
    max_price: float = None, # Optional filter: ?max_price=300000
    db: Session = Depends(get_db)
):
    """
    Return all listings.
    Optionally filter by location and/or max price using query parameters.
    Example: GET /listings?location=Siem Reap&max_price=250000
    """
    query = db.query(models.Listing)

    if location:
        query = query.filter(models.Listing.location == location)

    if max_price:
        query = query.filter(models.Listing.price <= max_price)

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


# Where uploaded images are saved on the server
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")

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
      2. Give the file a unique name (uuid) to avoid conflicts
      3. Save it to the uploads/ folder
      4. Update the listing's image_url to point to the new file
      5. Return the updated listing

    The image is then accessible at:
      http://localhost:8000/uploads/<filename>
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

    # Give the file a unique name using uuid (universally unique identifier)
    # This prevents name collisions if two listings both upload "photo.jpg"
    ext      = file.filename.rsplit('.', 1)[-1].lower()  # Get file extension
    filename = f"{uuid.uuid4().hex}.{ext}"               # e.g. "a3f9c12b....jpg"
    filepath = os.path.join(UPLOADS_DIR, filename)

    # Delete the old image if one exists (keeps the uploads folder clean)
    if listing.image_url:
        old_filename = listing.image_url.split("/uploads/")[-1]
        old_filepath = os.path.join(UPLOADS_DIR, old_filename)
        if os.path.exists(old_filepath):
            os.remove(old_filepath)

    # Save the new file to disk
    with open(filepath, "wb") as f:
        f.write(content)

    # Update the listing's image_url in the database
    # This is the URL the frontend will use to display the image
    listing.image_url = f"http://localhost:8000/uploads/{filename}"
    db.commit()
    db.refresh(listing)

    return listing
