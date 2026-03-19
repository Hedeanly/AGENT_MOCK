"""
routers/auth.py — Admin login and authentication

This handles:
  POST /auth/login → verify password, return a JWT token

What is a JWT token?
  After a successful login, we give the admin a "token" — a long
  encrypted string. The admin sends this token with every future
  request to prove they're logged in. We never store sessions on
  the server — the token itself contains the proof.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jose import jwt
from passlib.context import CryptContext
import os

import models
import schemas
from database import get_db
from routers.deps import get_current_admin as get_current_admin_dep

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth"])

# This tells passlib to use bcrypt for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = "HS256"  # The encryption algorithm for JWT tokens
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


def verify_password(plain: str, hashed: str) -> bool:
    """Check if a plain-text password matches a stored hash"""
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    """Turn a plain-text password into a secure hash"""
    return pwd_context.hash(plain)


def create_token(data: dict) -> str:
    """
    Create a JWT token.
    The token contains the username and an expiry time, encrypted with our SECRET_KEY.
    """
    payload = data.copy()
    expire  = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login", response_model=schemas.TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),  # Reads username+password from form fields
    db: Session = Depends(get_db)
):
    """
    Admin login.
    Accepts username + password, returns a JWT token if correct.

    Why OAuth2PasswordRequestForm?
      The Swagger UI /docs page sends login data as form fields (not JSON).
      This form handler makes the "Authorize" button in Swagger UI work properly.
      The frontend can also send JSON via the /auth/login endpoint directly.
    """
    # Look up the user by username
    user = db.query(models.User).filter(models.User.username == form.username).first()

    # If user doesn't exist OR password is wrong, return 401 Unauthorized
    # We give the same error for both cases — don't reveal which one failed
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create a token with the username inside it
    token = create_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_me(admin = Depends(get_current_admin_dep)):
    """
    Returns the currently logged-in admin's username.
    The frontend calls this to check if the stored token is still valid.
    If the token is expired or invalid, this returns 401.
    """
    return {"username": admin.username}
