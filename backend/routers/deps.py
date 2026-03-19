"""
routers/deps.py — Reusable dependencies (shared utilities for routes)

A "dependency" in FastAPI is a function that runs before a route handler.
You attach it to a route with Depends(...) and FastAPI calls it automatically.

The main dependency here is get_current_admin:
  - Reads the Authorization header from the request
  - Decodes and validates the JWT token
  - Returns the logged-in user if valid
  - Raises 401 Unauthorized if anything is wrong

Any route that uses Depends(get_current_admin) is automatically protected.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from dotenv import load_dotenv
import os

import models
from database import get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = "HS256"

# OAuth2PasswordBearer tells FastAPI:
#   "Expect a Bearer token in the Authorization header"
#   "If it's missing, point the user to /auth/login"
# This also makes the Swagger UI show a login button automatically!
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_admin(
    token: str = Depends(oauth2_scheme),  # Extracts the token from the request header
    db: Session = Depends(get_db)
) -> models.User:
    """
    Validates the JWT token and returns the current admin user.

    How it works:
      1. FastAPI extracts the token from the Authorization header
      2. We decode it using our SECRET_KEY
      3. We get the username from inside the token
      4. We look up that user in the database
      5. If anything fails, we return 401 Unauthorized

    Usage in a route:
      @router.post("/")
      def create_listing(admin = Depends(get_current_admin)):
          ...  # Only reachable if token is valid
    """

    # Standard 401 error — reused in multiple checks below
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},  # Standard header for auth errors
    )

    try:
        # Decode the token — this will raise JWTError if it's tampered or expired
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")  # "sub" is the standard JWT field for subject (username)

        if username is None:
            raise credentials_error

    except JWTError:
        # Token is invalid, expired, or tampered with
        raise credentials_error

    # Look up the user in the database
    user = db.query(models.User).filter(models.User.username == username).first()

    if user is None:
        raise credentials_error  # Token was valid but user no longer exists

    return user  # Route handler receives this user object
