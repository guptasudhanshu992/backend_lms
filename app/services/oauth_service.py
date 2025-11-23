"""
OAuth service for Google and LinkedIn authentication using Authlib.
Handles authorization code exchange, user account creation/linking.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from authlib.integrations.httpx_client import OAuth2Client
    AUTHLIB_AVAILABLE = True
except ImportError:
    AUTHLIB_AVAILABLE = False
    OAuth2Client = None

from app.config.settings import settings
from app.models import users
from app.services.d1_service import database
from app.core.security import hash_password
from app.services.email_service import send_security_notification

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication flows."""
    
    def __init__(self):
        if not AUTHLIB_AVAILABLE:
            logger.warning("Authlib not available - OAuth flows will not work")
        
        # Google OAuth configuration
        self.google_client_id = settings.GOOGLE_CLIENT_ID
        self.google_client_secret = settings.GOOGLE_CLIENT_SECRET
        self.google_redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.google_token_url = "https://oauth2.googleapis.com/token"
        self.google_userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # LinkedIn OAuth configuration
        self.linkedin_client_id = settings.LINKEDIN_CLIENT_ID
        self.linkedin_client_secret = settings.LINKEDIN_CLIENT_SECRET
        self.linkedin_redirect_uri = settings.LINKEDIN_REDIRECT_URI
        self.linkedin_auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.linkedin_token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.linkedin_userinfo_url = "https://api.linkedin.com/v2/userinfo"
    
    def get_google_auth_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL."""
        if not AUTHLIB_AVAILABLE:
            raise RuntimeError("Authlib not available")
        
        client = OAuth2Client(
            client_id=self.google_client_id,
            redirect_uri=self.google_redirect_uri,
        )
        
        authorization_url, _ = client.create_authorization_url(
            self.google_auth_url,
            scope="openid email profile",
            state=state,
        )
        return authorization_url
    
    def get_linkedin_auth_url(self, state: str) -> str:
        """Generate LinkedIn OAuth authorization URL."""
        if not AUTHLIB_AVAILABLE:
            raise RuntimeError("Authlib not available")
        
        client = OAuth2Client(
            client_id=self.linkedin_client_id,
            redirect_uri=self.linkedin_redirect_uri,
        )
        
        authorization_url, _ = client.create_authorization_url(
            self.linkedin_auth_url,
            scope="openid profile email",
            state=state,
        )
        return authorization_url
    
    def exchange_google_code(self, code: str) -> Dict[str, Any]:
        """Exchange Google authorization code for access token and user info."""
        if not AUTHLIB_AVAILABLE:
            raise RuntimeError("Authlib not available")
        
        client = OAuth2Client(
            client_id=self.google_client_id,
            client_secret=self.google_client_secret,
            redirect_uri=self.google_redirect_uri,
        )
        
        # Exchange code for token
        token = client.fetch_token(
            self.google_token_url,
            code=code,
            grant_type="authorization_code",
        )
        
        # Fetch user info
        resp = client.get(
            self.google_userinfo_url,
            token=token,
        )
        user_info = resp.json()
        
        return {
            "provider": "google",
            "provider_id": user_info["id"],
            "email": user_info["email"],
            "full_name": user_info.get("name", ""),
            "picture": user_info.get("picture", ""),
        }
    
    def exchange_linkedin_code(self, code: str) -> Dict[str, Any]:
        """Exchange LinkedIn authorization code for access token and user info."""
        if not AUTHLIB_AVAILABLE:
            raise RuntimeError("Authlib not available")
        
        client = OAuth2Client(
            client_id=self.linkedin_client_id,
            client_secret=self.linkedin_client_secret,
            redirect_uri=self.linkedin_redirect_uri,
        )
        
        # Exchange code for token
        token = client.fetch_token(
            self.linkedin_token_url,
            code=code,
            grant_type="authorization_code",
        )
        
        # Fetch user info
        resp = client.get(
            self.linkedin_userinfo_url,
            token=token,
        )
        user_info = resp.json()
        
        return {
            "provider": "linkedin",
            "provider_id": user_info["sub"],
            "email": user_info.get("email", ""),
            "full_name": user_info.get("name", ""),
            "picture": user_info.get("picture", ""),
        }
    
    def find_or_create_oauth_user(
        self, 
        oauth_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find existing user by OAuth provider or create new one.
        Returns user record.
        """
        provider = oauth_data["provider"]
        provider_id = oauth_data["provider_id"]
        email = oauth_data["email"]
        full_name = oauth_data["full_name"]
        picture = oauth_data.get("picture")
        
        # Check if user with this OAuth provider already exists
        query = users.select().where(
            (users.c.oauth_provider == provider) &
            (users.c.oauth_provider_id == provider_id)
        )
        existing_user = database.fetch_one(query)
        
        if existing_user:
            # User exists with this OAuth account
            logger.info(f"OAuth login: existing user {existing_user['email']} via {provider}")
            
            # Update last login
            update_query = users.update().where(
                users.c.id == existing_user["id"]
            ).values(
                last_login=datetime.utcnow(),
            )
            database.execute(update_query)
            
            return dict(existing_user)
        
        # Check if user with this email exists (link OAuth to existing account)
        query = users.select().where(users.c.email == email)
        existing_email_user = database.fetch_one(query)
        
        if existing_email_user:
            # Link OAuth provider to existing account
            logger.info(f"Linking {provider} OAuth to existing user {email}")
            
            update_query = users.update().where(
                users.c.id == existing_email_user["id"]
            ).values(
                oauth_provider=provider,
                oauth_provider_id=provider_id,
                profile_picture=picture or existing_email_user["profile_picture"],
                is_verified=True,  # OAuth emails are verified by provider
                last_login=datetime.utcnow(),
            )
            database.execute(update_query)
            
            # Send security notification about OAuth link
            try:
                send_security_notification(
                    email=email,
                    notification_type=f"{provider.title()} Account Linked",
                    details=f"Your {provider.title()} account was linked to your profile.",
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.error(f"Failed to send OAuth link notification: {e}")
            
            return dict(existing_email_user)
        
        # Create new user with OAuth
        logger.info(f"Creating new user via {provider} OAuth: {email}")
        
        # Generate random password (won't be used for OAuth login)
        import secrets
        random_password = secrets.token_urlsafe(32)
        hashed_password = hash_password(random_password)
        
        insert_query = users.insert().values(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role="student",  # Default role for new OAuth users
            is_active=True,
            is_verified=True,  # OAuth emails are pre-verified
            oauth_provider=provider,
            oauth_provider_id=provider_id,
            profile_picture=picture,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
        )
        
        user_id = database.execute(insert_query)
        
        # Fetch created user
        query = users.select().where(users.c.id == user_id)
        new_user = database.fetch_one(query)
        
        return dict(new_user)


# Singleton instance
oauth_service = OAuthService()
