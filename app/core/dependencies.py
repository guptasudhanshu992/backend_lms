from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.jwt import decode_token
from app.services.d1_service import database
from app import models
from typing import Optional
from types import SimpleNamespace
import json

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get current authenticated user from JWT token.
    Raises 401 if token is invalid or user not found.
    """
    import logging
    logger = logging.getLogger("lms.auth")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    logger.info(f"get_current_user: decoded payload = {payload}")
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    logger.info(f"get_current_user: user_id = {user_id}, type = {type(user_id)}")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Handle env-based admin (user_id = "0", not in database)
    if user_id == "0" or user_id == 0:
        # Check if this is admin from JWT
        if payload.get("role") == "admin":
            logger.info("get_current_user: returning env-based admin user")
            # Return a synthetic user object for env-based admin
            return SimpleNamespace(
                id=0,
                email=payload.get("email"),
                role="admin",
                is_active=True,
                is_verified=True,
                full_name="Admin User",
                created_at=None,
                consent=True,
                hashed_password=None,
                last_login=None
            )
    
    user = await database.fetch_one(
        models.users.select().where(models.users.c.id == int(user_id))
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_verified_user(current_user = Depends(get_current_user)):
    """Require verified email"""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


async def require_role(role: str):
    """Factory function to create role-based dependencies"""
    async def check_role(current_user = Depends(get_current_user)):
        if current_user.role != role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    return check_role


async def require_admin(current_user = Depends(get_current_user)):
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required"
        )
    return current_user


async def require_permission(permission: str, current_user = Depends(get_current_user)):
    """Check if user has specific permission through role, group, or user-level"""
    # Admin has all permissions
    if current_user.role == "admin":
        return current_user
    
    # Check role permissions
    role = await database.fetch_one(
        models.roles.select().where(models.roles.c.name == current_user.role)
    )
    if role:
        role_perms = json.loads(role.permissions) if isinstance(role.permissions, str) else role.permissions
        if "all" in role_perms or permission in role_perms:
            return current_user
    
    # Check user-level permissions
    user_perm = await database.fetch_one(
        models.user_permissions.select().where(
            models.user_permissions.c.user_id == current_user.id,
            models.user_permissions.c.permission == permission
        )
    )
    if user_perm:
        return current_user
    
    # Check group permissions
    user_groups = await database.fetch_all(
        models.user_groups.select().where(models.user_groups.c.user_id == current_user.id)
    )
    for ug in user_groups:
        group = await database.fetch_one(
            models.groups.select().where(models.groups.c.id == ug.group_id)
        )
        if group:
            group_perms = json.loads(group.permissions) if isinstance(group.permissions, str) else group.permissions
            if "all" in group_perms or permission in group_perms:
                return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Permission '{permission}' required"
    )


async def get_optional_user(request: Request) -> Optional[dict]:
    """Get user if authenticated, None otherwise (for optional auth)"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = await database.fetch_one(
        models.users.select().where(models.users.c.id == int(user_id))
    )
    return user
