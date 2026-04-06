

from pydantic import BaseModel
from typing import Optional
from datetime import datetime



class ListingCreate(BaseModel):
    """Used when CREATING a new listing (POST /listings)"""
    title:        str
    price:        float
    location:     str
    beds:         int
    baths:        int
    sqm:          int
    description:  Optional[str]   = None
    facilities:   Optional[str]   = None   # e.g. "Wifi,Pool,Gym"
    emoji:        Optional[str]   = "🏠"
    listing_type: Optional[str]   = "sale"  # "rent" or "sale"
    latitude:     Optional[float] = None
    longitude:    Optional[float] = None


class ListingUpdate(BaseModel):
    """Used when EDITING a listing (PUT /listings/{id}) — all fields optional"""
    title:        Optional[str]   = None
    price:        Optional[float] = None
    location:     Optional[str]   = None
    beds:         Optional[int]   = None
    baths:        Optional[int]   = None
    sqm:          Optional[int]   = None
    description:  Optional[str]   = None
    facilities:   Optional[str]   = None
    emoji:        Optional[str]   = None
    listing_type: Optional[str]   = None
    latitude:     Optional[float] = None
    longitude:    Optional[float] = None


class ListingResponse(BaseModel):
    """What the API returns when you request a listing"""
    id:           int
    title:        str
    price:        float
    location:     str
    beds:         int
    baths:        int
    sqm:          int
    description:  Optional[str]
    facilities:   Optional[str]
    emoji:        Optional[str]
    image_url:    Optional[str]
    listing_type: Optional[str]
    latitude:     Optional[float]
    longitude:    Optional[float]
    created_at:   datetime

    class Config:
        from_attributes = True  # Lets Pydantic read SQLAlchemy model objects directly


class LoginRequest(BaseModel):
    """Used when logging in (POST /auth/login)"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Returned after a successful login"""
    access_token: str
    token_type:   str = "bearer"  # Standard JWT token type



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
