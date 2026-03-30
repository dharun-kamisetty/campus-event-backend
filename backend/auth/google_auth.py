import os
import base64
import json
from fastapi import HTTPException, status
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "test-client-id")
ALLOWED_DOMAIN = "anurag.edu.in"

# Check if we're in test mode
IS_TEST_MODE = GOOGLE_CLIENT_ID == "test-client-id" or not GOOGLE_CLIENT_ID


async def verify_google_token(token: str) -> dict:
    """
    Verify Google OAuth token and extract user info.
    Enforces domain restriction to @anurag.edu.in
    
    Test Mode: When GOOGLE_CLIENT_ID is 'test-client-id', accepts test tokens
    in format: test_token_<base64_encoded_json>
    """
    # Test mode bypass - accept any test token
    if IS_TEST_MODE and token.startswith("test_token_"):
        try:
            # Parse test token: test_token_<base64>
            base64_data = token.replace("test_token_", "")
            json_data = base64.b64decode(base64_data).decode('utf-8')
            user_data = json.loads(json_data)
            
            email = user_data.get("email", "")
            if not email.endswith(f"@{ALLOWED_DOMAIN}"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Only {ALLOWED_DOMAIN} emails are allowed"
                )
            
            return {
                "email": email,
                "name": user_data.get("name", "Test User"),
                "picture": user_data.get("picture", "")
            }
        except Exception:
            # Fallback for simple test tokens
            return {
                "email": f"testuser@{ALLOWED_DOMAIN}",
                "name": "Test User",
                "picture": ""
            }
    
    # Real Google OAuth verification
    try:
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), GOOGLE_CLIENT_ID
        )

        # Extract email
        email = idinfo.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found in token"
            )

        # Domain restriction
        if not email.endswith(f"@{ALLOWED_DOMAIN}"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only {ALLOWED_DOMAIN} emails are allowed"
            )

        return {
            "email": email,
            "name": idinfo.get("name"),
            "picture": idinfo.get("picture")
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
