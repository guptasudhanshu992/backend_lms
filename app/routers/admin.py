from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.core.dependencies import require_admin, get_current_user
from app.services.d1_service import database
from app.services.permission_service import permission_service
from app.services.gdpr_service import gdpr_service
from app.models import users, roles, groups, sessions, audit_logs
from app.core.security import hash_password

router = APIRouter()


# ===== Request/Response Models =====

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class RoleCreate(BaseModel):
    name: str
    permissions: List[str]
    description: Optional[str] = None


class RoleUpdate(BaseModel):
    permissions: Optional[List[str]] = None
    description: Optional[str] = None


class GroupCreate(BaseModel):
    name: str
    permissions: List[str]
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    permissions: Optional[List[str]] = None
    description: Optional[str] = None


class PermissionGrant(BaseModel):
    user_id: int
    permission: str


class GroupMembership(BaseModel):
    user_id: int
    group_id: int


# ===== Auth Verification =====

@router.get('/me', dependencies=[Depends(require_admin)])
def get_current_admin(current_user: dict = Depends(get_current_user)):
    """Get current authenticated admin user info."""
    return {
        "id": current_user.get("user_id") or current_user.get("id"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "is_active": current_user.get("is_active", True),
    }


# ===== Dashboard Stats =====

@router.get('/stats', dependencies=[Depends(require_admin)])
def get_admin_stats():
    """Get dashboard statistics."""
    # Count total users
    total_users = database.fetch_val(
        query="SELECT COUNT(*) FROM users"
    )
    
    # Count active sessions (not revoked and not expired)
    active_sessions = database.fetch_val(
        query="SELECT COUNT(*) FROM sessions WHERE revoked = 0 AND expires_at > datetime('now')"
    )
    
    # Count audit logs
    total_audit_logs = database.fetch_val(
        query="SELECT COUNT(*) FROM audit_logs"
    )
    
    return {
        "total_users": total_users or 0,
        "active_sessions": active_sessions or 0,
        "audit_logs": total_audit_logs or 0,
        "total_courses": 6,  # Static for now
    }


# ===== User Management =====

@router.get('/users', dependencies=[Depends(require_admin)])
def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    """List all users with optional filters."""
    query = users.select()
    
    if role:
        query = query.where(users.c.role == role)
    if is_active is not None:
        query = query.where(users.c.is_active == is_active)
    
    query = query.offset(skip).limit(limit)
    
    result = database.fetch_all(query)
    return {
        "users": [
            {
                "id": u["id"],
                "email": u["email"],
                "full_name": u["full_name"],
                "role": u["role"],
                "is_active": u["is_active"],
                "is_verified": u["is_verified"],
                "oauth_provider": u["oauth_provider"],
                "created_at": u["created_at"].isoformat() if u["created_at"] else None,
                "last_login": u["last_login"].isoformat() if u["last_login"] else None,
            }
            for u in result
        ]
    }


@router.post('/users', dependencies=[Depends(require_admin)])
def create_user(payload: UserCreate):
    """Create a new user."""
    # Check if exists
    check_query = users.select().where(users.c.email == payload.email)
    existing = database.fetch_one(check_query)
    
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password
    hashed_password = hash_password(payload.password)
    
    # Create user
    insert_query = users.insert().values(
        email=payload.email,
        hashed_password=hashed_password,
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
        is_verified=True,  # Admin-created users are pre-verified
        created_at=datetime.utcnow(),
    )
    
    user_id = database.execute(insert_query)
    
    # Fetch created user
    query = users.select().where(users.c.id == user_id)
    user = database.fetch_one(query)
    
    return {"user": dict(user)}


@router.get('/users/{user_id}', dependencies=[Depends(require_admin)])
def get_user(user_id: int):
    """Get user details."""
    query = users.select().where(users.c.id == user_id)
    user = database.fetch_one(query)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"user": dict(user)}


@router.patch('/users/{user_id}', dependencies=[Depends(require_admin)])
def update_user(user_id: int, payload: UserUpdate):
    """Update user details."""
    update_values = {}
    
    if payload.full_name is not None:
        update_values["full_name"] = payload.full_name
    if payload.role is not None:
        update_values["role"] = payload.role
    if payload.is_active is not None:
        update_values["is_active"] = payload.is_active
    if payload.is_verified is not None:
        update_values["is_verified"] = payload.is_verified
    
    if not update_values:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_query = users.update().where(
        users.c.id == user_id
    ).values(**update_values)
    
    database.execute(update_query)
    
    # Fetch updated user
    query = users.select().where(users.c.id == user_id)
    user = database.fetch_one(query)
    
    return {"user": dict(user)}


@router.delete('/users/{user_id}', dependencies=[Depends(require_admin)])
def delete_user(user_id: int, hard_delete: bool = False):
    """Delete user account (soft delete by default)."""
    result = gdpr_service.delete_user_account(user_id, hard_delete=hard_delete)
    return result


# ===== Role Management =====

@router.get('/roles', dependencies=[Depends(require_admin)])
def list_roles():
    """List all roles."""
    import json
    result = permission_service.get_all_roles()
    # Parse permissions JSON string to array for frontend
    for role in result:
        if isinstance(role.get('permissions'), str):
            try:
                role['permissions'] = json.loads(role['permissions'])
            except:
                role['permissions'] = []
    return {"roles": result}


@router.post('/roles', dependencies=[Depends(require_admin)])
def create_role(payload: RoleCreate):
    """Create a new role."""
    try:
        role = permission_service.create_role(
            name=payload.name,
            permissions=payload.permissions,
            description=payload.description,
        )
        return {"role": role}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch('/roles/{role_id}', dependencies=[Depends(require_admin)])
def update_role(role_id: int, payload: RoleUpdate):
    """Update role permissions or description."""
    try:
        role = permission_service.update_role(
            role_id=role_id,
            permissions=payload.permissions,
            description=payload.description,
        )
        return {"role": role}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete('/roles/{role_id}', dependencies=[Depends(require_admin)])
def delete_role(role_id: int):
    """Delete a role."""
    try:
        permission_service.delete_role(role_id)
        return {"ok": True, "message": "Role deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Group Management =====

@router.get('/groups', dependencies=[Depends(require_admin)])
def list_groups():
    """List all groups."""
    result = permission_service.get_all_groups()
    return {"groups": result}


@router.post('/groups', dependencies=[Depends(require_admin)])
def create_group(payload: GroupCreate):
    """Create a new group."""
    group = permission_service.create_group(
        name=payload.name,
        permissions=payload.permissions,
        description=payload.description,
    )
    return {"group": group}


@router.patch('/groups/{group_id}', dependencies=[Depends(require_admin)])
def update_group(group_id: int, payload: GroupUpdate):
    """Update group permissions or description."""
    try:
        group = permission_service.update_group(
            group_id=group_id,
            permissions=payload.permissions,
            description=payload.description,
        )
        return {"group": group}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete('/groups/{group_id}', dependencies=[Depends(require_admin)])
def delete_group(group_id: int):
    """Delete a group."""
    permission_service.delete_group(group_id)
    return {"ok": True, "message": "Group deleted"}


@router.post('/groups/members', dependencies=[Depends(require_admin)])
def add_user_to_group(payload: GroupMembership):
    """Add user to a group."""
    permission_service.add_user_to_group(
        user_id=payload.user_id,
        group_id=payload.group_id,
    )
    return {"ok": True, "message": "User added to group"}


@router.delete('/groups/members', dependencies=[Depends(require_admin)])
def remove_user_from_group(payload: GroupMembership):
    """Remove user from a group."""
    permission_service.remove_user_from_group(
        user_id=payload.user_id,
        group_id=payload.group_id,
    )
    return {"ok": True, "message": "User removed from group"}


# ===== Permission Management =====

@router.post('/permissions/grant', dependencies=[Depends(require_admin)])
def grant_permission(payload: PermissionGrant):
    """Grant a permission to a user."""
    permission_service.grant_user_permission(
        user_id=payload.user_id,
        permission=payload.permission,
    )
    return {"ok": True, "message": "Permission granted"}


@router.post('/permissions/revoke', dependencies=[Depends(require_admin)])
def revoke_permission(payload: PermissionGrant):
    """Revoke a permission from a user."""
    permission_service.revoke_user_permission(
        user_id=payload.user_id,
        permission=payload.permission,
    )
    return {"ok": True, "message": "Permission revoked"}


@router.get('/permissions/user/{user_id}', dependencies=[Depends(require_admin)])
def get_user_permissions(user_id: int):
    """Get all permissions for a user."""
    perms = permission_service.get_user_permissions(user_id)
    return {"user_id": user_id, "permissions": list(perms)}


# ===== Session Management =====

@router.get('/sessions', dependencies=[Depends(require_admin)])
def list_sessions(
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
):
    """List all sessions with optional filters."""
    query = sessions.select()
    
    if user_id:
        query = query.where(sessions.c.user_id == user_id)
    if is_active is not None:
        query = query.where(sessions.c.is_active == is_active)
    
    query = query.order_by(sessions.c.created_at.desc()).offset(skip).limit(limit)
    
    result = database.fetch_all(query)
    return {
        "sessions": [
            {
                "id": s["id"],
                "user_id": s["user_id"],
                "ip_address": s["ip_address"],
                "user_agent": s["user_agent"],
                "device_type": s["device_type"],
                "browser": s["browser"],
                "os": s["os"],
                "is_active": s["is_active"],
                "created_at": s["created_at"].isoformat() if s["created_at"] else None,
                "last_activity": s["last_activity"].isoformat() if s["last_activity"] else None,
            }
            for s in result
        ]
    }


@router.post('/sessions/{session_id}/revoke', dependencies=[Depends(require_admin)])
def revoke_session(session_id: int):
    """Revoke a specific session."""
    update_query = sessions.update().where(
        sessions.c.id == session_id
    ).values(
        is_active=False,
        revoked_at=datetime.utcnow(),
    )
    database.execute(update_query)
    
    return {"ok": True, "message": "Session revoked"}


# ===== Audit Logs =====

@router.get('/audit-logs', dependencies=[Depends(require_admin)])
def list_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
):
    """List audit logs with optional filters."""
    import json
    query = audit_logs.select()
    
    if user_id:
        query = query.where(audit_logs.c.user_id == user_id)
    if action:
        query = query.where(audit_logs.c.action == action)
    
    query = query.order_by(audit_logs.c.created_at.desc()).offset(skip).limit(limit)
    
    result = database.fetch_all(query)
    return {
        "logs": [
            {
                "id": log["id"],
                "user_id": log["user_id"],
                "action": log["action"],
                "ip_address": log["ip"],
                "user_agent": log["user_agent"],
                "meta": json.loads(log["meta"]) if log["meta"] else {},
                "timestamp": log["created_at"].isoformat() if log["created_at"] else None,
            }
            for log in result
        ]
    }
