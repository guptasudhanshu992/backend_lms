import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # App
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    DEBUG: bool = os.getenv("DEBUG", "1") == "1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    
    # JWT & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "please-set-a-secure-secret-change-this-in-production")
    ACCESS_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "900"))
    REFRESH_TOKEN_EXPIRE_SECONDS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_SECONDS", "604800"))
    
    # Admin Bootstrap
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@lms.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Gratitude@2025")
    
    # Email/SMTP
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@lms.example.com")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "1") == "1"
    
    # OAuth - Google
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/google/callback")
    
    # OAuth - LinkedIn
    LINKEDIN_CLIENT_ID: str = os.getenv("LINKEDIN_CLIENT_ID", "")
    LINKEDIN_CLIENT_SECRET: str = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    LINKEDIN_REDIRECT_URI: str = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/api/auth/oauth/linkedin/callback")
    
    # Cloudflare R2
    R2_ENDPOINT: str = os.getenv("R2_ENDPOINT", "https://<account_id>.r2.cloudflarestorage.com")
    R2_ACCESS_KEY: str = os.getenv("R2_ACCESS_KEY", "")
    R2_SECRET_KEY: str = os.getenv("R2_SECRET_KEY", "")
    R2_BUCKET: str = os.getenv("R2_BUCKET", "my-bucket")
    
    # Cloudflare Stream
    CF_ACCOUNT_ID: str = os.getenv("CF_ACCOUNT_ID", "")
    CF_STREAM_TOKEN: str = os.getenv("CF_STREAM_TOKEN", "")



@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
