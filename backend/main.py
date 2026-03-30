from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import auth, venues, requests, ai

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="University Venue Booking System",
    description="Backend API for venue booking with Google OAuth authentication and AI-powered recommendations",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(venues.router)
app.include_router(requests.router)
app.include_router(ai.router)


@app.get("/")
async def root():
    return {
        "message": "University Venue Booking API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
