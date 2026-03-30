from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# Venue Schemas
class VenueBase(BaseModel):
    name: str
    capacity: int
    location: str
    logistics: Optional[str] = None


class VenueCreate(VenueBase):
    pass


class VenueResponse(VenueBase):
    id: int
    status: str

    class Config:
        from_attributes = True


# Venue Request Schemas
class VenueRequestBase(BaseModel):
    venue_id: Optional[int] = None
    event_name: str
    department: str
    purpose: str
    requested_date: str
    start_time: str
    end_time: str
    proposal_letter_url: Optional[str] = None


class VenueRequestCreate(VenueRequestBase):
    pass


class VenueRequestResponse(VenueRequestBase):
    id: int
    requested_by: int
    status: str
    admin_comment: Optional[str] = None
    seen_by_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Admin Action Schemas
class AdminActionRequest(BaseModel):
    admin_comment: Optional[str] = None
