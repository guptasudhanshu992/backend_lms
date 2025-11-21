import os
from functools import lru_cache


class Settings:
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    R2_ENDPOINT: str = os.getenv("R2_ENDPOINT", "https://<account_id>.r2.cloudflarestorage.com")
    R2_ACCESS_KEY: str = os.getenv("R2_ACCESS_KEY", "")
    R2_SECRET_KEY: str = os.getenv("R2_SECRET_KEY", "")
    R2_BUCKET: str = os.getenv("R2_BUCKET", "my-bucket")

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

    CF_ACCOUNT_ID: str = os.getenv("CF_ACCOUNT_ID", "")
    CF_STREAM_TOKEN: str = os.getenv("CF_STREAM_TOKEN", "")


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
