"""Admin bootstrap service - creates admin user from .env on startup"""
import logging
from app.config.settings import settings
from app.core.security import hash_password
from app.services.d1_service import database
from app import models

logger = logging.getLogger("lms.admin")


async def bootstrap_admin():
    """
    Create admin user from environment variables if it doesn't exist.
    This runs on application startup.
    """
    try:
        # Check if admin already exists
        admin_query = models.users.select().where(
            models.users.c.email == settings.ADMIN_EMAIL
        )
        existing_admin = await database.fetch_one(admin_query)
        
        if existing_admin:
            logger.info(f"Admin user already exists: {settings.ADMIN_EMAIL}")
            return existing_admin
        
        # Create admin user
        hashed_password = hash_password(settings.ADMIN_PASSWORD)
        
        insert_query = models.users.insert().values(
            email=settings.ADMIN_EMAIL,
            hashed_password=hashed_password,
            is_active=True,
            is_verified=True,
            role="admin",
            consent=True
        )
        
        user_id = await database.execute(insert_query)
        logger.info(f"✅ Admin user created: {settings.ADMIN_EMAIL} (ID: {user_id})")
        
        # Fetch and return the created user
        new_admin = await database.fetch_one(
            models.users.select().where(models.users.c.id == user_id)
        )
        
        return new_admin
        
    except Exception as e:
        logger.error(f"Failed to bootstrap admin user: {e}")
        raise
