from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db
from backend.models import VenueRequest, User, Venue
from backend.schemas import (
    VenueRequestCreate,
    VenueRequestResponse,
    AdminActionRequest
)
from backend.auth.dependencies import get_current_admin, get_current_active_user
from backend.utils.mailer import send_approval_email, send_rejection_email

router = APIRouter(prefix="/requests", tags=["Venue Requests"])


@router.post("/", response_model=VenueRequestResponse)
async def create_request(
    request: VenueRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new venue booking request (student/club/faculty)"""
    new_request = VenueRequest(
        **request.dict(),
        requested_by=current_user.id
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


@router.get("/", response_model=List[VenueRequestResponse])
async def list_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List venue requests.
    - Admin: sees all requests
    - Others: see only their own requests
    """
    query = db.query(VenueRequest)
    
    # Role-based filtering
    if current_user.role != "admin":
        query = query.filter(VenueRequest.requested_by == current_user.id)
    
    # Status filtering
    if status_filter:
        query = query.filter(VenueRequest.status == status_filter)
    
    return query.all()


@router.get("/{request_id}", response_model=VenueRequestResponse)
async def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific request.
    - Admin: marks as seen
    - User: can only view their own
    """
    request = db.query(VenueRequest).filter(VenueRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Authorization check
    if current_user.role != "admin" and request.requested_by != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Mark as seen by admin
    if current_user.role == "admin" and not request.seen_by_admin:
        request.seen_by_admin = True
        db.commit()
        db.refresh(request)
    
    return request


@router.post("/{request_id}/approve", response_model=VenueRequestResponse)
async def approve_request(
    request_id: int,
    action: AdminActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Approve a venue request (admin only)"""
    request = db.query(VenueRequest).filter(VenueRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = "approved"
    request.admin_comment = action.admin_comment
    request.seen_by_admin = True
    
    db.commit()
    db.refresh(request)
    
    # Send email notification to user
    user = db.query(User).filter(User.id == request.requested_by).first()
    venue = db.query(Venue).filter(Venue.id == request.venue_id).first()
    if user and venue:
        await send_approval_email(
            user_email=user.email,
            event_name=request.event_name,
            venue_name=venue.name,
            date=request.requested_date,
            time=f"{request.start_time} - {request.end_time}",
            admin_comment=action.admin_comment
        )
    
    return request


@router.post("/{request_id}/reject", response_model=VenueRequestResponse)
async def reject_request(
    request_id: int,
    action: AdminActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Reject a venue request (admin only)"""
    request = db.query(VenueRequest).filter(VenueRequest.id == request_id).first()
    
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    request.status = "rejected"
    request.admin_comment = action.admin_comment
    request.seen_by_admin = True
    
    db.commit()
    db.refresh(request)
    
    # Send email notification to user
    user = db.query(User).filter(User.id == request.requested_by).first()
    if user:
        await send_rejection_email(
            user_email=user.email,
            event_name=request.event_name,
            date=request.requested_date,
            admin_comment=action.admin_comment
        )
    
    return request
