from fastapi import APIRouter, Depends, HTTPException, Request, Response, Cookie
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import secrets

from app.services import auth_service
from app.services.d1_service import database
from app.services.email_service import send_password_reset_email, send_security_notification
from app.services.oauth_service import oauth_service
from app.config.settings import settings
from app.models import users, password_reset_tokens, email_verification_tokens
from app.core.jwt import create_reset_token, decode_token
from app.core.security import hash_password

router = APIRouter()


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    consent: bool = False


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post('/register')
async def register(payload: RegisterIn):
    try:
        user = await auth_service.register_user(payload.email, payload.password, payload.consent)
        return {"ok": True, "user": {"id": user.id, "email": user.email}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/login')
async def login(payload: LoginIn, request: Request, response: Response):
    data = await auth_service.authenticate_user(payload.email, payload.password, user_agent=request.headers.get('user-agent'), ip=request.client.host)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Fetch user data to return in response
    user_query = users.select().where(users.c.email == payload.email)
    user_data = await database.fetch_one(user_query)
    
    # set refresh token as httpOnly cookie
    response.set_cookie("refresh_token", data['refresh_token'], httponly=True, secure=not settings.DEBUG, samesite='lax')
    
    return {
        "access_token": data['access_token'],
        "refresh_token": data['refresh_token'],
        "token_type": "bearer",
        "user": {
            "id": user_data["id"],
            "email": user_data["email"],
            "full_name": user_data["full_name"],
            "role": user_data["role"],
            "is_active": user_data["is_active"],
            "is_verified": user_data["is_verified"],
        }
    }


@router.post('/refresh')
async def refresh(response: Response, refresh_token: str | None = Cookie(None)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    data = await auth_service.refresh_tokens(refresh_token)
    if not data:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    response.set_cookie("refresh_token", data['refresh_token'], httponly=True, secure=not settings.DEBUG, samesite='lax')
    return {"access_token": data['access_token'], "token_type": "bearer"}


@router.post('/logout')
async def logout(response: Response, refresh_token: str | None = Cookie(None)):
    if refresh_token:
        await auth_service.logout(refresh_token)
    response.delete_cookie("refresh_token")
    return {"ok": True}


@router.post('/forgot-password')
async def forgot_password(
    email: EmailStr,
    request: Request,
):
    """
    Send password reset email with token.
    Always returns success to prevent user enumeration.
    """
    # Find user by email
    query = users.select().where(users.c.email == email)
    user = await database.fetch_one(query)
    
    if user:
        # Generate reset token (1 hour expiry)
        token = create_reset_token(user_id=user["id"])
        
        # Store token in database
        insert_query = password_reset_tokens.insert().values(
            user_id=user["id"],
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow(),
        )
        await database.execute(insert_query)
        
        # Send reset email
        try:
            await send_password_reset_email(
                email=user["email"],
                reset_token=token,
            )
        except Exception as e:
            # Log but don't fail - don't reveal if email exists
            import logging
            logging.error(f"Failed to send password reset email: {e}")
    
    # Always return success to prevent user enumeration
    return {"ok": True, "message": "If the email exists, a reset link has been sent"}


@router.post('/reset-password')
async def reset_password(
    token: str,
    new_password: str,
    request: Request,
):
    """
    Reset password using token from email.
    """
    # Decode and validate token
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Check token exists in database and not used
    query = password_reset_tokens.select().where(
        (password_reset_tokens.c.token == token) &
        (password_reset_tokens.c.user_id == user_id) &
        (password_reset_tokens.c.used_at == None) &
        (password_reset_tokens.c.expires_at > datetime.utcnow())
    )
    token_record = await database.fetch_one(query)
    
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Get user
    user_query = users.select().where(users.c.id == user_id)
    user = await database.fetch_one(user_query)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    hashed_password = hash_password(new_password)
    update_query = users.update().where(
        users.c.id == user_id
    ).values(
        hashed_password=hashed_password,
    )
    await database.execute(update_query)
    
    # Mark token as used
    mark_used_query = password_reset_tokens.update().where(
        password_reset_tokens.c.id == token_record["id"]
    ).values(
        used_at=datetime.utcnow(),
    )
    await database.execute(mark_used_query)
    
    # Send security notification
    try:
        await send_security_notification(
            email=user["email"],
            notification_type="Password Changed",
            details="Your password was successfully reset.",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception as e:
        import logging
        logging.error(f"Failed to send security notification: {e}")
    
    return {"ok": True, "message": "Password reset successful"}


@router.get('/verify-email')
async def verify_email(token: str):
    """
    Verify email address using token from email.
    """
    # Decode token
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Check token exists and not used
    query = email_verification_tokens.select().where(
        (email_verification_tokens.c.token == token) &
        (email_verification_tokens.c.user_id == user_id) &
        (email_verification_tokens.c.used_at == None) &
        (email_verification_tokens.c.expires_at > datetime.utcnow())
    )
    token_record = await database.fetch_one(query)
    
    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Update user as verified
    update_query = users.update().where(
        users.c.id == user_id
    ).values(
        is_verified=True,
    )
    await database.execute(update_query)
    
    # Mark token as used
    mark_used_query = email_verification_tokens.update().where(
        email_verification_tokens.c.id == token_record["id"]
    ).values(
        used_at=datetime.utcnow(),
    )
    await database.execute(mark_used_query)
    
    return {"ok": True, "message": "Email verified successfully"}


@router.get('/oauth/google')
async def oauth_google_login():
    """
    Redirect to Google OAuth authorization.
    """
    state = secrets.token_urlsafe(32)
    # TODO: Store state in session/redis for CSRF protection
    try:
        auth_url = oauth_service.get_google_auth_url(state)
        return {"auth_url": auth_url}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/oauth/google/callback')
async def oauth_google_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
):
    """
    Handle Google OAuth callback.
    """
    # TODO: Validate state for CSRF protection
    
    try:
        # Exchange code for user info
        oauth_data = await oauth_service.exchange_google_code(code)
        
        # Find or create user
        user = await oauth_service.find_or_create_oauth_user(
            oauth_data=oauth_data,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
        
        # Generate tokens
        data = await auth_service.authenticate_user(
            user["email"],
            None,  # No password needed for OAuth
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host,
            oauth_user=user,
        )
        
        if not data:
            raise HTTPException(status_code=500, detail="Failed to authenticate OAuth user")
        
        # Set refresh token cookie
        response.set_cookie(
            "refresh_token",
            data["refresh_token"],
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
        )
        
        # Redirect to frontend with access token
        frontend_redirect = f"{settings.FRONTEND_ORIGIN}/oauth-callback?access_token={data['access_token']}"
        return {"redirect_url": frontend_redirect}
        
    except Exception as e:
        import logging
        logging.exception("OAuth Google callback failed")
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")


@router.get('/oauth/linkedin')
async def oauth_linkedin_login():
    """
    Redirect to LinkedIn OAuth authorization.
    """
    state = secrets.token_urlsafe(32)
    # TODO: Store state in session/redis for CSRF protection
    try:
        auth_url = oauth_service.get_linkedin_auth_url(state)
        return {"auth_url": auth_url}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/oauth/linkedin/callback')
async def oauth_linkedin_callback(
    code: str,
    state: str,
    request: Request,
    response: Response,
):
    """
    Handle LinkedIn OAuth callback.
    """
    # TODO: Validate state for CSRF protection
    
    try:
        # Exchange code for user info
        oauth_data = await oauth_service.exchange_linkedin_code(code)
        
        # Find or create user
        user = await oauth_service.find_or_create_oauth_user(
            oauth_data=oauth_data,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
        )
        
        # Generate tokens
        data = await auth_service.authenticate_user(
            user["email"],
            None,  # No password needed for OAuth
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host,
            oauth_user=user,
        )
        
        if not data:
            raise HTTPException(status_code=500, detail="Failed to authenticate OAuth user")
        
        # Set refresh token cookie
        response.set_cookie(
            "refresh_token",
            data["refresh_token"],
            httponly=True,
            secure=not settings.DEBUG,
            samesite="lax",
        )
        
        # Redirect to frontend with access token
        frontend_redirect = f"{settings.FRONTEND_ORIGIN}/oauth-callback?access_token={data['access_token']}"
        return {"redirect_url": frontend_redirect}
        
    except Exception as e:
        import logging
        logging.exception("OAuth LinkedIn callback failed")
        raise HTTPException(status_code=500, detail=f"OAuth failed: {str(e)}")
