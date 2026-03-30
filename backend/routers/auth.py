from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import UserResponse
from backend.auth.google_auth import verify_google_token
from backend.auth.jwt_utils import create_access_token
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    token: str
    role: Optional[str] = "student"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/google", response_model=TokenResponse)
async def google_login(
    token_request: GoogleTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Google OAuth login endpoint.
    Verifies Google token, creates/updates user, returns JWT.
    For testing: role can be passed to set user role (admin, faculty, club, student)
    """
    # Verify Google token and get user info
    user_info = await verify_google_token(token_request.token)
    
    # Check if user exists
    user = db.query(User).filter(User.email == user_info["email"]).first()
    
    if not user:
        # Create new user - use provided role or default to student
        user = User(
            email=user_info["email"],
            name=user_info["name"],
            role=token_request.role or "student"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


class CreateAdminRequest(BaseModel):
    email: str
    name: str


@router.post("/create-admin", response_model=TokenResponse)
async def create_admin(
    request: CreateAdminRequest,
    db: Session = Depends(get_db)
):
    """
    Create an admin user. Only one admin can exist for security.
    Call this once to set up the initial admin account.
    """
    import os
    admin_secret = os.getenv("ADMIN_SECRET", "")
    
    # Check if admin already exists
    existing_admin = db.query(User).filter(User.role == "admin").first()
    
    if existing_admin:
        # Update existing admin's email to new one
        existing_admin.email = request.email
        existing_admin.name = request.name
        db.commit()
        db.refresh(existing_admin)
        access_token = create_access_token(data={"sub": existing_admin.email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": existing_admin
        }
    
    # Create new admin
    admin_user = User(
        email=request.email,
        name=request.name,
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    access_token = create_access_token(data={"sub": admin_user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": admin_user
    }
