from sqlalchemy.orm import Session
from backend.database import engine, SessionLocal, Base
from backend.models import Venue

venues_data = [
    {"name": "Main Auditorium", "capacity": 500, "location": "Block A, Ground Floor", "logistics": '{"projector": true, "sound_system": true, "ac": true, "stage": true}', "status": "available"},
    {"name": "Conference Hall A", "capacity": 100, "location": "Block B, 1st Floor", "logistics": '{"projector": true, "sound_system": true, "ac": true, "whiteboard": true}', "status": "available"},
    {"name": "Seminar Room 101", "capacity": 50, "location": "Block C, Ground Floor", "logistics": '{"projector": true, "ac": true, "whiteboard": true}', "status": "available"},
    {"name": "Workshop Lab 1", "capacity": 80, "location": "Block D, 2nd Floor", "logistics": '{"projector": true, "ac": true, "computers": true, "wifi": true}', "status": "available"},
    {"name": "Cultural Stage", "capacity": 300, "location": "Open Air Theater", "logistics": '{"stage": true, "sound_system": true, "lighting": true}', "status": "available"},
]

def init_venues():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Venue).count()
        if existing > 0:
            print(f"Database already has {existing} venues. Skipping initialization.")
            return
        
        for venue_data in venues_data:
            venue = Venue(**venue_data)
            db.add(venue)
        
        db.commit()
        print(f"Successfully initialized {len(venues_data)} venues!")
    except Exception as e:
        db.rollback()
        print(f"Error initializing venues: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_venues()