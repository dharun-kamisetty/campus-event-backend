from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import UserResponse
from backend.auth.google_auth import verify_google_token
from backend.auth.jwt_utils import create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    token: str


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
    """
    # Verify Google token and get user info
    user_info = await verify_google_token(token_request.token)
    
    # Check if user exists
    user = db.query(User).filter(User.email == user_info["email"]).first()
    
    if not user:
        # Create new user with default role
        user = User(
            email=user_info["email"],
            name=user_info["name"],
            role="student"  # Default role
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
