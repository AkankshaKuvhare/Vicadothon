import os
import jwt
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Set auto_error=False to let our dependency handle missing headers conditionally
security = HTTPBearer(auto_error=False)

def get_current_user_id(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    FastAPI security dependency. Extracts Bearer token from headers,
    verifies it against SUPABASE_JWT_SECRET, and returns user_id (sub).
    If database integration is NOT active, returns a dummy fallback user ID for offline testing.
    """
    from app import supabase_db
    
    # If Supabase variables are not configured, bypass authentication checks
    if not supabase_db.is_db_configured():
        return "00000000-0000-0000-0000-000000000000"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials are required to access this endpoint."
        )

    token = credentials.credentials
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
    
    if not jwt_secret:
        print("[AUTH_ERROR] DB is active but SUPABASE_JWT_SECRET is missing from backend/.env!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth configuration error: SUPABASE_JWT_SECRET is missing."
        )

    try:
        # Decode Supabase JWT signed with HS256
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": True},
            audience="authenticated"
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject (sub) claim."
            )
            
        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please sign in again."
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
