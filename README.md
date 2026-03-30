# Campus Event Backend

FastAPI backend for the Campus Event Management System with Google OAuth authentication and AI-powered venue recommendations.

## Features

- Google OAuth authentication
- Venue management (CRUD)
- Request booking system
- AI-powered venue recommendations (Groq API)
- Admin dashboard for request approval

## Tech Stack

- **Framework:** FastAPI
- **Database:** SQLite
- **AI:** Groq API (Llama 3.3)
- **Auth:** JWT tokens

## Setup

### Local Development

```bash
# Install dependencies
pip install uv
uv sync

# Run the server
uvicorn backend.main:app --reload --port 8000
```

### Environment Variables

Create a `.env` file with:

```
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

Get your Groq API key from: https://console.groq.com

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/google` | Google OAuth login |
| GET | `/venues/` | List all venues |
| POST | `/venues/` | Create venue (admin) |
| GET | `/requests/` | List requests |
| POST | `/requests/` | Create request |
| POST | `/requests/{id}/approve` | Approve request (admin) |
| POST | `/requests/{id}/reject` | Reject request (admin) |
| POST | `/ai/recommend-venues` | Get AI recommendations |

## Deploy to Render

1. Connect this repo to Render
2. Set environment variables in Render dashboard
3. Deploy!

The app runs on port `$PORT` (set by Render).

## API Documentation

Once running, visit:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## License

© 2026 Anurag University - AU GLUG