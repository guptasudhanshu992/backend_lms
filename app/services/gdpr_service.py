"""
GDPR compliance service for data export and account deletion.
"""
import logging
import json
from typing import Dict, Any
from datetime import datetime

from app.models import users, sessions, audit_logs
from app.services.d1_service import database

logger = logging.getLogger(__name__)


class GDPRService:
    """Service for GDPR compliance features."""
    
    async def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        Export all user data in machine-readable format (GDPR Article 20).
        Returns comprehensive JSON with user info, sessions, audit logs.
        """
        # Get user data
        user_query = users.select().where(users.c.id == user_id)
        user = await database.fetch_one(user_query)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        user_data = {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "is_active": user["is_active"],
            "is_verified": user["is_verified"],
            "oauth_provider": user["oauth_provider"],
            "profile_picture": user["profile_picture"],
            "created_at": user["created_at"].isoformat() if user["created_at"] else None,
            "last_login": user["last_login"].isoformat() if user["last_login"] else None,
            "two_factor_enabled": user["two_factor_enabled"],
            "consent": user["consent"],
        }
        
        # Get session history
        sessions_query = sessions.select().where(
            sessions.c.user_id == user_id
        ).order_by(sessions.c.created_at.desc())
        session_records = await database.fetch_all(sessions_query)
        
        sessions_data = [
            {
                "id": session["id"],
                "ip_address": session["ip_address"],
                "user_agent": session["user_agent"],
                "device_type": session["device_type"],
                "browser": session["browser"],
                "os": session["os"],
                "location": session["location"],
                "is_active": session["is_active"],
                "created_at": session["created_at"].isoformat() if session["created_at"] else None,
                "last_activity": session["last_activity"].isoformat() if session["last_activity"] else None,
                "revoked_at": session["revoked_at"].isoformat() if session["revoked_at"] else None,
            }
            for session in session_records
        ]
        
        # Get audit logs
        audit_query = audit_logs.select().where(
            audit_logs.c.user_id == user_id
        ).order_by(audit_logs.c.timestamp.desc())
        audit_records = await database.fetch_all(audit_query)
        
        audit_data = [
            {
                "id": log["id"],
                "action": log["action"],
                "ip_address": log["ip_address"],
                "user_agent": log["user_agent"],
                "metadata": log["metadata"],
                "timestamp": log["timestamp"].isoformat() if log["timestamp"] else None,
            }
            for log in audit_records
        ]
        
        # Compile full export
        export = {
            "export_date": datetime.utcnow().isoformat(),
            "user": user_data,
            "sessions": sessions_data,
            "audit_logs": audit_data,
            "export_format_version": "1.0",
        }
        
        logger.info(f"GDPR data export generated for user {user_id}")
        return export
    
    async def delete_user_account(
        self,
        user_id: int,
        hard_delete: bool = False,
    ) -> Dict[str, Any]:
        """
        Delete user account (GDPR Article 17 - Right to Erasure).
        
        Args:
            user_id: User ID to delete
            hard_delete: If True, permanently delete from DB.
                        If False (default), soft delete (deactivate + anonymize).
        
        Returns:
            Dict with deletion details
        """
        # Get user
        user_query = users.select().where(users.c.id == user_id)
        user = await database.fetch_one(user_query)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        if hard_delete:
            # HARD DELETE - Permanently remove all data
            logger.warning(f"HARD DELETE initiated for user {user_id}")
            
            # Delete sessions
            delete_sessions = sessions.delete().where(
                sessions.c.user_id == user_id
            )
            await database.execute(delete_sessions)
            
            # Anonymize audit logs (keep for compliance but remove PII)
            anonymize_audit = audit_logs.update().where(
                audit_logs.c.user_id == user_id
            ).values(
                user_id=None,  # Remove user reference
                ip_address="<deleted>",
                user_agent="<deleted>",
            )
            await database.execute(anonymize_audit)
            
            # Delete user
            delete_user = users.delete().where(users.c.id == user_id)
            await database.execute(delete_user)
            
            logger.info(f"User {user_id} HARD DELETED")
            return {
                "deleted": True,
                "user_id": user_id,
                "deletion_type": "hard",
                "deleted_at": datetime.utcnow().isoformat(),
            }
        
        else:
            # SOFT DELETE - Deactivate and anonymize
            logger.info(f"SOFT DELETE (anonymization) initiated for user {user_id}")
            
            # Anonymize user data
            anonymize_user = users.update().where(
                users.c.id == user_id
            ).values(
                email=f"deleted_user_{user_id}@deleted.local",
                full_name="[Deleted User]",
                hashed_password="",
                is_active=False,
                is_verified=False,
                oauth_provider=None,
                oauth_provider_id=None,
                profile_picture=None,
                two_factor_secret=None,
                two_factor_enabled=False,
                consent=False,
            )
            await database.execute(anonymize_user)
            
            # Revoke all sessions
            revoke_sessions = sessions.update().where(
                sessions.c.user_id == user_id
            ).values(
                is_active=False,
                revoked_at=datetime.utcnow(),
            )
            await database.execute(revoke_sessions)
            
            # Anonymize audit logs
            anonymize_audit = audit_logs.update().where(
                audit_logs.c.user_id == user_id
            ).values(
                ip_address="<anonymized>",
                user_agent="<anonymized>",
            )
            await database.execute(anonymize_audit)
            
            logger.info(f"User {user_id} SOFT DELETED (anonymized)")
            return {
                "deleted": True,
                "user_id": user_id,
                "deletion_type": "soft",
                "anonymized_at": datetime.utcnow().isoformat(),
                "note": "Account deactivated and personal data anonymized",
            }
    
    async def get_consent_status(self, user_id: int) -> Dict[str, Any]:
        """Get user's consent status."""
        user_query = users.select().where(users.c.id == user_id)
        user = await database.fetch_one(user_query)
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        return {
            "user_id": user_id,
            "consent_given": user["consent"],
            "created_at": user["created_at"].isoformat() if user["created_at"] else None,
        }
    
    async def update_consent(
        self,
        user_id: int,
        consent: bool,
    ) -> Dict[str, Any]:
        """Update user's consent status."""
        update_query = users.update().where(
            users.c.id == user_id
        ).values(
            consent=consent,
        )
        await database.execute(update_query)
        
        logger.info(f"User {user_id} consent updated to: {consent}")
        
        return {
            "user_id": user_id,
            "consent": consent,
            "updated_at": datetime.utcnow().isoformat(),
        }


# Singleton instance
gdpr_service = GDPRService()
