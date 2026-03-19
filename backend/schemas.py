"""
schemas.py — Data validation shapes (Pydantic models)

While models.py defines what the DATABASE looks like,
schemas.py defines what the API accepts and returns.

Think of schemas as forms:
  - "Create" schemas = the form you fill in to add something
  - "Response" schemas = what you get back after a request

Pydantic automatically validates incoming data — if someone
sends a string where a number is expected, it rejects it with
a clear error message.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────
# LISTING SCHEMAS
# ─────────────────────────────────────────────

class ListingCreate(BaseModel):
    """Used when CREATING a new listing (POST /listings)"""
    title:       str
    price:       float
    location:    str
    beds:        int
    baths:       int
    sqm:         int
    description: Optional[str] = None
    facilities:  Optional[str] = None   # e.g. "Wifi,Pool,Gym"
    emoji:       Optional[str] = "🏠"


class ListingUpdate(BaseModel):
    """Used when EDITING a listing (PUT /listings/{id}) — all fields optional"""
    title:       Optional[str]   = None
    price:       Optional[float] = None
    location:    Optional[str]   = None
    beds:        Optional[int]   = None
    baths:       Optional[int]   = None
    sqm:         Optional[int]   = None
    description: Optional[str]   = None
    facilities:  Optional[str]   = None
    emoji:       Optional[str]   = None


class ListingResponse(BaseModel):
    """What the API returns when you request a listing"""
    id:          int
    title:       str
    price:       float
    location:    str
    beds:        int
    baths:       int
    sqm:         int
    description: Optional[str]
    facilities:  Optional[str]
    emoji:       Optional[str]
    image_url:   Optional[str]
    created_at:  datetime

    class Config:
        from_attributes = True  # Lets Pydantic read SQLAlchemy model objects directly


# ─────────────────────────────────────────────
# AUTH SCHEMAS
# ─────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Used when logging in (POST /auth/login)"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Returned after a successful login"""
    access_token: str
    token_type:   str = "bearer"  # Standard JWT token type


# ─────────────────────────────────────────────
# ENQUIRY SCHEMAS
# ─────────────────────────────────────────────

class EnquiryCreate(BaseModel):
    """Used when submitting an enquiry (POST /enquiries)"""
    listing_id: int
    name:       str
    phone:      Optional[str] = None
    email:      str
    message:    Optional[str] = None


class EnquiryResponse(BaseModel):
    """What the API returns for an enquiry"""
    id:            int
    listing_id:    int
    listing_title: Optional[str] = None  # Joined from the listings table — friendlier than just an ID
    name:          str
    phone:         Optional[str]
    email:         str
    message:       Optional[str]
    created_at:    datetime

    class Config:
        from_attributes = True
