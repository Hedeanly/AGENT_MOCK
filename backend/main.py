"""
main.py — The entry point for the NestKH backend API

This is the file you run to start the server.
It creates the FastAPI app, connects all the routers,
and sets up the database tables on first run.

To start the server:
  cd backend
  venv/Scripts/uvicorn main:app --reload

Then visit:
  http://localhost:8000/docs   ← Interactive API explorer (Swagger UI)
  http://localhost:8000        ← Basic health check
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base, SessionLocal
from routers import listings, auth, enquiries
import models

# ─────────────────────────────────────────────
# CREATE THE APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="NestKH API",
    description="Backend API for NestKH — Premium Properties in Cambodia",
    version="1.0.0"
)

# ─────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing)
# This allows the frontend (running on a different port)
# to make requests to the backend. Without this, the
# browser would block the requests for security reasons.
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # In production, replace * with your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],       # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# REGISTER ROUTERS
# Each router handles a section of the API
# ─────────────────────────────────────────────

app.include_router(listings.router)
app.include_router(auth.router)
app.include_router(enquiries.router)

# ─────────────────────────────────────────────
# CREATE DATABASE TABLES
# This runs on startup — creates all tables defined
# in models.py if they don't already exist.
# Safe to run multiple times (won't overwrite data).
# ─────────────────────────────────────────────

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# SEED INITIAL DATA
# On first run, create the default admin user
# and add the 6 sample listings from the mockup
# ─────────────────────────────────────────────

def seed_data():
    db = SessionLocal()

    # Only seed if the database is empty
    if db.query(models.User).count() > 0:
        db.close()
        return

    print("Seeding database with initial data...")

    # Import here to avoid circular imports
    from routers.auth import hash_password
    from dotenv import load_dotenv
    import os
    load_dotenv()

    # Create the default admin user
    admin = models.User(
        username=os.getenv("ADMIN_USERNAME", "admin"),
        hashed_password=hash_password(os.getenv("ADMIN_PASSWORD", "admin123"))
    )
    db.add(admin)

    # Add the 6 sample listings from the original mockup
    sample_listings = [
        models.Listing(
            title="Modern Villa with Private Pool", price=320000,
            location="Phnom Penh", beds=4, baths=3, sqm=380,
            emoji="🏡", facilities="Wifi,Parking,Pool,Gym,Security,Garden",
            description="A stunning modern villa featuring an open-plan living area, chef's kitchen, and private pool. Located in a prestigious gated community with 24-hour security."
        ),
        models.Listing(
            title="Riverside Panorama Apartment", price=185000,
            location="Phnom Penh", beds=2, baths=2, sqm=120,
            emoji="🏢", facilities="Wifi,Parking,Gym,Concierge,Balcony",
            description="Bright and airy apartment with sweeping river views on the 18th floor. Features floor-to-ceiling windows and a rooftop infinity pool."
        ),
        models.Listing(
            title="French Colonial Heritage Home", price=475000,
            location="Phnom Penh", beds=5, baths=4, sqm=600,
            emoji="🏛️", facilities="Parking,Garden,Security",
            description="A beautifully restored French colonial villa in the historic heart of the city. Featuring original wooden floors, soaring ceilings, and a tropical garden."
        ),
        models.Listing(
            title="Boutique Villa near Angkor Wat", price=210000,
            location="Siem Reap", beds=3, baths=2, sqm=250,
            emoji="🌴", facilities="Wifi,Pool,Parking,Garden",
            description="Charming boutique villa just 5 minutes from the ancient temples of Angkor. Private plunge pool and outdoor dining sala."
        ),
        models.Listing(
            title="Hilltop Retreat with Sea Views", price=155000,
            location="Kampot", beds=3, baths=2, sqm=200,
            emoji="🌅", facilities="Wifi,Garden,Solar,Parking",
            description="A serene hilltop property with breathtaking views across the Gulf of Thailand. Entirely solar-powered and surrounded by nature."
        ),
        models.Listing(
            title="Luxury Penthouse, 28th Floor", price=390000,
            location="Phnom Penh", beds=3, baths=3, sqm=290,
            emoji="🌆", facilities="Wifi,Gym,Pool,Concierge,Parking,Balcony",
            description="Extraordinary full-floor penthouse commanding a 360° panorama of Phnom Penh. Private rooftop terrace and dedicated concierge service."
        ),
    ]

    db.add_all(sample_listings)
    db.commit()
    db.close()
    print("Done! Database seeded.")

seed_data()


# ─────────────────────────────────────────────
# ROOT ENDPOINT
# A simple health check so you know the server is running
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "NestKH API is running", "docs": "/docs"}
