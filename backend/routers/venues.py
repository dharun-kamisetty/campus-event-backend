from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db
from backend.models import Venue
from backend.schemas import VenueCreate, VenueResponse
from backend.auth.dependencies import get_current_admin, get_current_active_user

router = APIRouter(prefix="/venues", tags=["Venues"])


@router.get("/", response_model=List[VenueResponse])
async def list_venues(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all venues (authenticated users)"""
    venues = db.query(Venue).all()
    return venues


@router.post("/", response_model=VenueResponse)
async def create_venue(
    venue: VenueCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create a new venue (admin only)"""
    new_venue = Venue(**venue.dict())
    db.add(new_venue)
    db.commit()
    db.refresh(new_venue)
    return new_venue


@router.put("/{venue_id}", response_model=VenueResponse)
async def update_venue(
    venue_id: int,
    venue: VenueCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update venue (admin only)"""
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    for key, value in venue.dict().items():
        setattr(db_venue, key, value)
    
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.delete("/{venue_id}")
async def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Delete venue (admin only)"""
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    db.delete(db_venue)
    db.commit()
    return {"message": "Venue deleted successfully"}
