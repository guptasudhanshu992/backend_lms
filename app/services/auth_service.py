from app.config.settings import settings
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.services import session_service, audit_service, email_service
from app import models
from app.services.d1_service import database
import uuid
import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


def register_user(email: str, password: str, consent: bool = False):
    # check exists
    q = models.users.select().where(models.users.c.email == email)
    exists = database.fetch_one(q)
    if exists:
        raise ValueError("User already exists")
    
    hashed = hash_password(password)
    
    try:
        # Insert the new user
        insert_query = models.users.insert().values(
            email=email, 
            hashed_password=hashed, 
            is_active=True, 
            is_verified=False, 
            consent=consent, 
            role='student'
        )
        user_id = database.execute(insert_query)
        
        # Fetch the newly created user
        if user_id:
            user = database.fetch_one(models.users.select().where(models.users.c.id == user_id))
        else:
            # Try fetching by email as fallback
            user = database.fetch_one(models.users.select().where(models.users.c.email == email))
        
        if not user:
            raise ValueError("Failed to retrieve created user")
        
        # send verification email asynchronously
        token = create_refresh_token(str(user["id"]))
        verify_link = f"{settings.FRONTEND_ORIGIN}/verify-email?token={token}"
        
        # Send email in background without blocking registration
        async def send_verification_email_async():
            try:
                await asyncio.to_thread(
                    email_service.send_email,
                    email,
                    "Verify your account",
                    f"Click to verify: {verify_link}"
                )
                logger.info(f"Verification email sent to {email}")
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")
        
        # Schedule the async task without awaiting
        try:
            asyncio.create_task(send_verification_email_async())
        except RuntimeError:
            # If no event loop is running, log and continue
            logger.warning("Could not schedule email task - no event loop running")
        
        # Log audit event
        try:
            audit_service.log(user_id=user["id"], action="user.register", meta={})
        except Exception as e:
            print(f"Failed to log audit: {e}")
        
        return user
        
    except ValueError:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise ValueError(f"Failed to create user: {str(e)}")


def authenticate_user(email: str, password: str = None, user_agent: str = None, ip: str = None, oauth_user: dict = None):
    """
    Authenticate user with email/password or OAuth.
    If oauth_user is provided, skip password verification.
    """
    if oauth_user:
        # OAuth authentication - user already validated
        user = oauth_user
    else:
        # Regular email/password authentication
        q = models.users.select().where(models.users.c.email == email)
        user = database.fetch_one(q)
        if not user:
            audit_service.log(None, "auth.failure", {"email": email, "reason": "not_found"})
            return None
        if not user["hashed_password"]:
            return None
        if not verify_password(password, user["hashed_password"]):
            audit_service.log(user["id"], "auth.failure", {"reason": "invalid_password"})
            return None

    # create session
    session = session_service.create_session(user_id=user["id"], user_agent=user_agent, ip=ip)
    access = create_access_token(str(user["id"]), expires_delta=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    refresh = create_refresh_token(str(user["id"]), expires_delta=settings.REFRESH_TOKEN_EXPIRE_SECONDS)
    audit_service.log(user["id"], "auth.success", {"session_id": session})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def refresh_tokens(refresh_token: str):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    user_id = payload.get("sub")
    access = create_access_token(str(user_id), expires_delta=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    refresh = create_refresh_token(str(user_id), expires_delta=settings.REFRESH_TOKEN_EXPIRE_SECONDS)
    audit_service.log(user_id, "auth.refresh", {})
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


def logout(refresh_token: str):
    # We don't store JWT server-side in this demo, but we can mark sessions revoked if we pass session id
    payload = decode_token(refresh_token)
    if not payload:
        return False
    user_id = payload.get("sub")
    audit_service.log(user_id, "auth.logout", {})
    return True
