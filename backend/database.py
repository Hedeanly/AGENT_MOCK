"""
database.py — Sets up the database connection

SQLAlchemy is the library we use to talk to the database.
Instead of writing raw SQL queries, SQLAlchemy lets us use
Python classes and objects to interact with the database.

Think of it like this:
  - engine     = the actual connection to the database file
  - SessionLocal = a "session" (one open conversation with the DB)
  - Base       = the parent class all our table models will inherit from
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load variables from the .env file into the environment
load_dotenv()

# Get the database URL from .env
# Locally:     sqlite:///./nestkh.db  (a local file)
# On Render:   postgresql://user:pass@host/dbname  (cloud database)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nestkh.db")

# Render's PostgreSQL URLs start with "postgres://" (old format)
# but SQLAlchemy requires "postgresql://" — fix it automatically
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; PostgreSQL doesn't need any extra args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Create the engine — this is the actual connection to the database
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# SessionLocal is a factory — each time we call it, we get a new DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all our database models (tables)
Base = declarative_base()


# This function is used in our API routes to get a database session
# It opens a session, gives it to the route, then closes it when done
def get_db():
    db = SessionLocal()
    try:
        yield db       # "yield" gives the session to whoever called this function
    finally:
        db.close()     # Always close the session after use (even if an error occurs)
