"""
models.py — Database table definitions

Each class here represents one table in the database.
SQLAlchemy reads these classes and creates the actual tables for us.

Think of each class as a blueprint for a table:
  - Class name  = table name
  - Each Column = one column in the table
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class Listing(Base):
    """
    The 'listings' table — stores all property listings.
    Each row = one property.
    """
    __tablename__ = "listings"

    id          = Column(Integer, primary_key=True, index=True)  # Unique ID, auto-increments
    title       = Column(String(200), nullable=False)            # Property name
    price       = Column(Float, nullable=False)                  # Price in USD
    location    = Column(String(100), nullable=False)            # City (Phnom Penh, etc.)
    beds        = Column(Integer, nullable=False)                # Number of bedrooms
    baths       = Column(Integer, nullable=False)                # Number of bathrooms
    sqm         = Column(Integer, nullable=False)                # Size in square metres
    description = Column(Text, nullable=True)                    # Long text description
    facilities  = Column(String(500), nullable=True)             # Comma-separated: "Wifi,Pool,Gym"
    emoji       = Column(String(10), nullable=True)              # Display emoji e.g. 🏡
    image_url   = Column(String(500), nullable=True)             # Path to uploaded image
    created_at  = Column(DateTime, server_default=func.now())    # Auto-set when created


class User(Base):
    """
    The 'users' table — stores admin accounts.
    For now there will only be one admin, but this scales to multiple.
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(100), unique=True, nullable=False)  # Must be unique
    hashed_password = Column(String(200), nullable=False)               # Never store plain passwords!
    created_at      = Column(DateTime, server_default=func.now())


class Enquiry(Base):
    """
    The 'enquiries' table — stores messages submitted via the enquiry form.
    Each row = one enquiry from a potential buyer.
    """
    __tablename__ = "enquiries"

    id         = Column(Integer, primary_key=True, index=True)
    listing_id = Column(Integer, nullable=False)          # Which property they're asking about
    name       = Column(String(100), nullable=False)      # Buyer's name
    phone      = Column(String(50), nullable=True)        # Buyer's phone
    email      = Column(String(100), nullable=False)      # Buyer's email
    message    = Column(Text, nullable=True)              # Their message
    created_at = Column(DateTime, server_default=func.now())
