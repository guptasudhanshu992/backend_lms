"""
Permission management service for RBAC.
Handles roles, groups, user permissions, and permission checking.
"""
import logging
from typing import List, Optional, Set
from datetime import datetime

from app.models import (
    roles, groups, user_groups, user_permissions,
    users
)
from app.services.d1_service import database

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing roles, groups, and permissions."""
    
    async def get_role_by_name(self, role_name: str) -> Optional[dict]:
        """Get role by name."""
        query = roles.select().where(roles.c.name == role_name)
        role = await database.fetch_one(query)
        return dict(role) if role else None
    
    async def get_all_roles(self) -> List[dict]:
        """Get all roles."""
        query = roles.select()
        result = await database.fetch_all(query)
        return [dict(row) for row in result]
    
    async def create_role(
        self,
        name: str,
        permissions: List[str],
        description: Optional[str] = None,
    ) -> dict:
        """Create a new role."""
        # Check if role exists
        existing = await self.get_role_by_name(name)
        if existing:
            raise ValueError(f"Role '{name}' already exists")
        
        # Convert permissions list to JSON string
        import json
        permissions_json = json.dumps(permissions)
        
        insert_query = roles.insert().values(
            name=name,
            permissions=permissions_json,
            description=description,
            created_at=datetime.utcnow(),
        )
        role_id = await database.execute(insert_query)
        
        # Fetch created role
        query = roles.select().where(roles.c.id == role_id)
        role = await database.fetch_one(query)
        return dict(role)
    
    async def update_role(
        self,
        role_id: int,
        permissions: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Update role permissions or description."""
        update_values = {}
        
        if permissions is not None:
            import json
            update_values["permissions"] = json.dumps(permissions)
        
        if description is not None:
            update_values["description"] = description
        
        if not update_values:
            raise ValueError("No updates provided")
        
        update_query = roles.update().where(
            roles.c.id == role_id
        ).values(**update_values)
        await database.execute(update_query)
        
        # Fetch updated role
        query = roles.select().where(roles.c.id == role_id)
        role = await database.fetch_one(query)
        return dict(role)
    
    async def delete_role(self, role_id: int) -> bool:
        """Delete a role (only if no users have it)."""
        # Check if any users have this role
        query = users.select().where(users.c.role == role_id)
        users_with_role = await database.fetch_one(query)
        
        if users_with_role:
            raise ValueError("Cannot delete role - users are assigned to it")
        
        delete_query = roles.delete().where(roles.c.id == role_id)
        await database.execute(delete_query)
        return True
    
    async def get_all_groups(self) -> List[dict]:
        """Get all groups."""
        query = groups.select()
        result = await database.fetch_all(query)
        return [dict(row) for row in result]
    
    async def create_group(
        self,
        name: str,
        permissions: List[str],
        description: Optional[str] = None,
    ) -> dict:
        """Create a new group."""
        import json
        permissions_json = json.dumps(permissions)
        
        insert_query = groups.insert().values(
            name=name,
            permissions=permissions_json,
            description=description,
            created_at=datetime.utcnow(),
        )
        group_id = await database.execute(insert_query)
        
        # Fetch created group
        query = groups.select().where(groups.c.id == group_id)
        group = await database.fetch_one(query)
        return dict(group)
    
    async def update_group(
        self,
        group_id: int,
        permissions: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Update group permissions or description."""
        update_values = {}
        
        if permissions is not None:
            import json
            update_values["permissions"] = json.dumps(permissions)
        
        if description is not None:
            update_values["description"] = description
        
        if not update_values:
            raise ValueError("No updates provided")
        
        update_query = groups.update().where(
            groups.c.id == group_id
        ).values(**update_values)
        await database.execute(update_query)
        
        # Fetch updated group
        query = groups.select().where(groups.c.id == group_id)
        group = await database.fetch_one(query)
        return dict(group)
    
    async def delete_group(self, group_id: int) -> bool:
        """Delete a group."""
        # Delete all user memberships
        delete_memberships = user_groups.delete().where(
            user_groups.c.group_id == group_id
        )
        await database.execute(delete_memberships)
        
        # Delete group
        delete_query = groups.delete().where(groups.c.id == group_id)
        await database.execute(delete_query)
        return True
    
    async def add_user_to_group(self, user_id: int, group_id: int) -> bool:
        """Add user to a group."""
        # Check if already member
        query = user_groups.select().where(
            (user_groups.c.user_id == user_id) &
            (user_groups.c.group_id == group_id)
        )
        existing = await database.fetch_one(query)
        
        if existing:
            return True  # Already member
        
        insert_query = user_groups.insert().values(
            user_id=user_id,
            group_id=group_id,
            created_at=datetime.utcnow(),
        )
        await database.execute(insert_query)
        return True
    
    async def remove_user_from_group(self, user_id: int, group_id: int) -> bool:
        """Remove user from a group."""
        delete_query = user_groups.delete().where(
            (user_groups.c.user_id == user_id) &
            (user_groups.c.group_id == group_id)
        )
        await database.execute(delete_query)
        return True
    
    async def get_user_groups(self, user_id: int) -> List[dict]:
        """Get all groups a user belongs to."""
        query = """
        SELECT g.* FROM groups g
        JOIN user_groups ug ON g.id = ug.group_id
        WHERE ug.user_id = :user_id
        """
        result = await database.fetch_all(query=query, values={"user_id": user_id})
        return [dict(row) for row in result]
    
    async def grant_user_permission(
        self,
        user_id: int,
        permission: str,
    ) -> bool:
        """Grant a specific permission to a user."""
        # Check if already granted
        query = user_permissions.select().where(
            (user_permissions.c.user_id == user_id) &
            (user_permissions.c.permission == permission)
        )
        existing = await database.fetch_one(query)
        
        if existing:
            return True  # Already granted
        
        insert_query = user_permissions.insert().values(
            user_id=user_id,
            permission=permission,
            created_at=datetime.utcnow(),
        )
        await database.execute(insert_query)
        return True
    
    async def revoke_user_permission(
        self,
        user_id: int,
        permission: str,
    ) -> bool:
        """Revoke a specific permission from a user."""
        delete_query = user_permissions.delete().where(
            (user_permissions.c.user_id == user_id) &
            (user_permissions.c.permission == permission)
        )
        await database.execute(delete_query)
        return True
    
    async def get_user_permissions(self, user_id: int) -> Set[str]:
        """
        Get all permissions for a user (from role + groups + individual).
        Returns a set of permission strings.
        """
        all_permissions = set()
        
        # Get user's role permissions
        query = """
        SELECT r.permissions FROM roles r
        JOIN users u ON u.role = r.name
        WHERE u.id = :user_id
        """
        role_result = await database.fetch_one(query=query, values={"user_id": user_id})
        
        if role_result and role_result["permissions"]:
            import json
            try:
                role_perms = json.loads(role_result["permissions"])
                all_permissions.update(role_perms)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse role permissions for user {user_id}")
        
        # Get group permissions
        user_group_list = await self.get_user_groups(user_id)
        for group in user_group_list:
            if group["permissions"]:
                import json
                try:
                    group_perms = json.loads(group["permissions"])
                    all_permissions.update(group_perms)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse group permissions for group {group['id']}")
        
        # Get individual user permissions
        query = user_permissions.select().where(
            user_permissions.c.user_id == user_id
        )
        user_perms = await database.fetch_all(query)
        all_permissions.update([perm["permission"] for perm in user_perms])
        
        return all_permissions
    
    async def check_user_permission(
        self,
        user_id: int,
        required_permission: str,
    ) -> bool:
        """Check if user has a specific permission."""
        user_perms = await self.get_user_permissions(user_id)
        return required_permission in user_perms


# Singleton instance
permission_service = PermissionService()
