from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from app.config.settings import settings
from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import verify_password, hash_password

router = APIRouter()

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post('/login')
async def admin_login(payload: AdminLoginRequest):
    """
    Admin login using credentials from .env file.
    Does not require database lookup.
    """
    import logging
    logger = logging.getLogger("lms.admin_auth")
    
    logger.info(f"Login attempt - Email from request: {payload.email}")
    logger.info(f"Login attempt - Expected email: {settings.ADMIN_EMAIL}")
    logger.info(f"Login attempt - Expected password: {settings.ADMIN_PASSWORD}")
    
    # Validate against .env credentials
    if payload.email != settings.ADMIN_EMAIL:
        logger.warning(f"Email mismatch: {payload.email} != {settings.ADMIN_EMAIL}")
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    # For env-based password, we compare directly (not hashed in env)
    # In production, you might want to hash the env password as well
    if payload.password != settings.ADMIN_PASSWORD:
        logger.warning(f"Password mismatch")
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    
    # Create tokens with extra claims for email and role
    extra_claims = {
        "email": payload.email,
        "role": "admin"
    }
    
    access_token = create_access_token("0", extra_claims=extra_claims)
    refresh_token = create_refresh_token("0", extra_claims=extra_claims)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": 0,
            "email": payload.email,
            "role": "admin",
            "full_name": "Admin User"
        }
    }
