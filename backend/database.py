"""
  - engine     = the actual connection to the database file
  - SessionLocal = a "session" (one open conversation with the DB)
  - Base       = the parent class all our table models will inherit from
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nestkh.db")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


# This function is used in our API routes to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db       # "yield" gives the session to whoever called this function
    finally:
        db.close()     # Always close the session after use (even if an error occurs)
