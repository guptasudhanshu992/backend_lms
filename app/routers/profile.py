from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging

from app.core.dependencies import get_current_user
from app.services.d1_service import database
from app.core.security import hash_password, verify_password
from app.models import users
from app.services import audit_service

router = APIRouter()
logger = logging.getLogger(__name__)


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class EmailChange(BaseModel):
    new_email: EmailStr
    password: str


@router.get('/me')
def get_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile."""
    try:
        query = users.select().where(users.c.id == current_user["id"])
        user = database.fetch_one(query)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user["id"],
            "email": user["email"],
            "full_name": user.get("full_name"),
            "profile_picture": user.get("profile_picture"),
            "role": user.get("role", "student"),
            "is_active": user.get("is_active", False),
            "is_verified": user.get("is_verified", False),
            "two_factor_enabled": user.get("two_factor_enabled", False),
            "oauth_provider": user.get("oauth_provider"),
            "created_at": user["created_at"].isoformat() if user.get("created_at") else None,
            "last_login": user["last_login"].isoformat() if user.get("last_login") else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")


@router.put('/me')
def update_profile(
    payload: ProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile."""
    try:
        update_data = {}
        
        if payload.full_name is not None:
            update_data["full_name"] = payload.full_name
        
        if payload.profile_picture is not None:
            update_data["profile_picture"] = payload.profile_picture
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow()
        
        query = users.update().where(users.c.id == current_user["id"]).values(**update_data)
        database.execute(query)
        
        # Log audit event
        audit_service.log(
            user_id=current_user["id"],
            action="profile.update",
            meta={"fields": list(update_data.keys())}
        )
        
        # Fetch updated user
        updated_user = database.fetch_one(users.select().where(users.c.id == current_user["id"]))
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": updated_user["id"],
                "email": updated_user["email"],
                "full_name": updated_user.get("full_name"),
                "profile_picture": updated_user.get("profile_picture"),
                "role": updated_user.get("role"),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.post('/change-password')
def change_password(
    payload: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user's password."""
    try:
        # Fetch user with password
        query = users.select().where(users.c.id == current_user["id"])
        user = database.fetch_one(query)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has a password (might be OAuth user)
        if not user.get("hashed_password"):
            raise HTTPException(
                status_code=400, 
                detail="Cannot change password for OAuth accounts"
            )
        
        # Verify current password
        if not verify_password(payload.current_password, user["hashed_password"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Validate new password
        if len(payload.new_password) < 8:
            raise HTTPException(
                status_code=400,
                detail="New password must be at least 8 characters long"
            )
        
        # Hash and update new password
        new_hashed = hash_password(payload.new_password)
        update_query = users.update().where(users.c.id == current_user["id"]).values(
            hashed_password=new_hashed,
            updated_at=datetime.utcnow()
        )
        database.execute(update_query)
        
        # Log audit event
        audit_service.log(
            user_id=current_user["id"],
            action="password.change",
            meta={}
        )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.post('/change-email')
def change_email(
    payload: EmailChange,
    current_user: dict = Depends(get_current_user)
):
    """Change user's email address."""
    try:
        # Fetch user
        query = users.select().where(users.c.id == current_user["id"])
        user = database.fetch_one(query)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password
        if user.get("hashed_password"):
            if not verify_password(payload.password, user["hashed_password"]):
                raise HTTPException(status_code=400, detail="Password is incorrect")
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot change email for OAuth accounts without password"
            )
        
        # Check if new email already exists
        existing = database.fetch_one(
            users.select().where(users.c.email == payload.new_email)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        
        # Update email and mark as unverified
        update_query = users.update().where(users.c.id == current_user["id"]).values(
            email=payload.new_email,
            is_verified=False,
            updated_at=datetime.utcnow()
        )
        database.execute(update_query)
        
        # Log audit event
        audit_service.log(
            user_id=current_user["id"],
            action="email.change",
            meta={"old_email": user["email"], "new_email": payload.new_email}
        )
        
        # TODO: Send verification email to new address
        
        return {
            "message": "Email changed successfully. Please verify your new email address.",
            "new_email": payload.new_email
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to change email")


@router.delete('/me')
def delete_account(
    password: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete user's account (soft delete by deactivating)."""
    try:
        # Fetch user
        query = users.select().where(users.c.id == current_user["id"])
        user = database.fetch_one(query)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify password if user has one
        if user.get("hashed_password"):
            if not verify_password(password, user["hashed_password"]):
                raise HTTPException(status_code=400, detail="Password is incorrect")
        
        # Soft delete by deactivating
        update_query = users.update().where(users.c.id == current_user["id"]).values(
            is_active=False,
            updated_at=datetime.utcnow()
        )
        database.execute(update_query)
        
        # Log audit event
        audit_service.log(
            user_id=current_user["id"],
            action="account.delete",
            meta={}
        )
        
        return {"message": "Account deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete account")
