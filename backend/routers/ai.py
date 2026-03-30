import os
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from groq import Groq, GroqError
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Venue
from backend.auth.dependencies import get_current_active_user
from backend.models import User

router = APIRouter(prefix="/ai", tags=["AI"])


class VenueRecommendationRequest(BaseModel):
    event_name: str
    event_type: str
    expected_attendees: int
    duration_hours: int
    requirements: List[str] = []
    preferred_location: Optional[str] = None
    date: Optional[str] = None


class VenueRecommendation(BaseModel):
    venue_name: str
    venue_id: int
    score: int
    reason: str
    availability: str


class AIRecommendationResponse(BaseModel):
    recommendations: List[VenueRecommendation]
    model_used: str


SYSTEM_PROMPT = """You are a venue booking expert for Anurag University.
Your task is to analyze event requirements and recommend the most suitable venues.

Available Venues:
{venues_json}

Instructions:
1. First, check if the venue has SUFFICIENT capacity (should be >= expected attendees)
2. Check if the venue has the REQUIRED facilities
3. Consider the preferred location if specified
4. Score each venue 0-100 based on overall suitability

Scoring Criteria:
- Capacity match (40%): Must have capacity >= expected attendees
- Facilities match (35%): How many required facilities are available
- Location preference (15%): If preferred location specified, bonus points
- Availability (10%): Available venues score higher

Respond ONLY with valid JSON in this exact format:
{{
  "recommendations": [
    {{
      "venue_name": "exact venue name from the list",
      "venue_id": venue id number,
      "score": 0-100,
      "reason": "brief 1-2 sentence explanation of why this venue is suitable",
      "availability": "available" or "unavailable"
    }}
  ]
}}

IMPORTANT: 
- Only recommend venues from the provided list
- Maximum 3 recommendations
- Sort by score (highest first)
- Must be valid JSON - no markdown, no additional text
- If no venue meets requirements, return empty recommendations array
"""


def get_groq_client():
    """Get Groq client with API key from environment"""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your-groq-api-key-here":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GROQ_API_KEY not configured. Please add your API key to .env file."
        )
    return Groq(api_key=api_key)


def venues_to_json(venues: List[Venue]) -> str:
    """Convert venue database models to JSON string for AI"""
    venue_list = []
    for venue in venues:
        logistics = {}
        if venue.logistics:
            try:
                logistics = json.loads(venue.logistics) if isinstance(venue.logistics, str) else venue.logistics
            except (json.JSONDecodeError, AttributeError):
                logistics = {}
        
        venue_list.append({
            "id": venue.id,
            "name": venue.name,
            "capacity": venue.capacity,
            "location": venue.location,
            "status": venue.status,
            "logistics": logistics
        })
    return json.dumps(venue_list, indent=2)


async def get_venue_recommendations(
    event_details: dict,
    venues: List[Venue],
    client: Groq
) -> List[dict]:
    """Call Groq API to get venue recommendations"""
    
    venues_json = venues_to_json(venues)
    
    user_message = f"""Event Requirements:
- Event Name: {event_details['event_name']}
- Event Type: {event_details['event_type']}
- Expected Attendees: {event_details['expected_attendees']}
- Duration: {event_details['duration_hours']} hours
- Required Facilities: {', '.join(event_details['requirements']) if event_details['requirements'] else 'None specified'}
- Preferred Location: {event_details.get('preferred_location', 'No preference')}
- Requested Date: {event_details.get('date', 'Any date')}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(venues_json=venues_json)},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        response_text = response.choices[0].message.content
        
        # Parse the JSON response
        try:
            result = json.loads(response_text)
            return result.get("recommendations", [])
        except json.JSONDecodeError:
            # If AI returns invalid JSON, try to extract JSON
            return []
            
    except GroqError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Groq API error: {str(e)}"
        )


@router.post("/recommend-venues", response_model=AIRecommendationResponse)
async def recommend_venues(
    request: VenueRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    client: Groq = Depends(get_groq_client)
):
    """
    AI-Powered Venue Recommendation
    
    Get intelligent venue recommendations based on your event requirements.
    Uses Groq's llama-3.3-70b-versatile model to analyze:
    - Venue capacity vs expected attendees
    - Required facilities and amenities
    - Location preferences
    - Availability
    
    Returns top 3 venue recommendations with scores and reasons.
    """
    
    # Get all available venues
    venues = db.query(Venue).filter(Venue.status == "available").all()
    
    if not venues:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No venues available for booking"
        )
    
    # Prepare event details for AI
    event_details = {
        "event_name": request.event_name,
        "event_type": request.event_type,
        "expected_attendees": request.expected_attendees,
        "duration_hours": request.duration_hours,
        "requirements": request.requirements,
        "preferred_location": request.preferred_location,
        "date": request.date
    }
    
    # Get AI recommendations
    ai_recommendations = await get_venue_recommendations(event_details, venues, client)
    
    # Convert to response format
    recommendations = []
    for rec in ai_recommendations[:3]:  # Limit to top 3
        recommendations.append(VenueRecommendation(
            venue_name=rec.get("venue_name", ""),
            venue_id=rec.get("venue_id", 0),
            score=rec.get("score", 0),
            reason=rec.get("reason", ""),
            availability=rec.get("availability", "unknown")
        ))
    
    return AIRecommendationResponse(
        recommendations=recommendations,
        model_used="llama-3.3-70b-versatile"
    )


@router.get("/models")
async def list_available_models(current_user: User = Depends(get_current_active_user)):
    """List available AI models (for documentation)"""
    return {
        "available_models": [
            {
                "name": "llama-3.3-70b-versatile",
                "description": "Latest Llama model - best for complex reasoning",
                "recommended": True
            },
            {
                "name": "mixtral-8x7b-32768", 
                "description": "Fast inference with large context",
                "recommended": False
            },
            {
                "name": "llama-3.1-70b-versatile",
                "description": "Previous version of Llama 3.1",
                "recommended": False
            }
        ],
        "current_model": "llama-3.3-70b-versatile"
    }


@router.get("/health")
async def ai_health_check():
    """Check if AI service is configured"""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key or api_key == "your-groq-api-key-here":
        return {
            "status": "not_configured",
            "message": "GROQ_API_KEY not set. Please add your API key to .env file.",
            "get_key_url": "https://console.groq.com"
        }
    
    return {
        "status": "ready",
        "message": "AI service is configured and ready"
    }
