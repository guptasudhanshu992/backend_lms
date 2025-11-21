import boto3
from botocore.client import Config
from app.config.settings import settings


def create_r2_client():
    # R2 is S3-compatible; set endpoint_url to R2 endpoint
    # If R2 endpoint is not configured or contains a placeholder value, do not create client now.
    if not settings.R2_ENDPOINT or "<" in settings.R2_ENDPOINT or ">" in settings.R2_ENDPOINT:
        return None

    session = boto3.session.Session()
    client = session.client(
        "s3",
        region_name="auto",
        endpoint_url=settings.R2_ENDPOINT,
        aws_access_key_id=settings.R2_ACCESS_KEY,
        aws_secret_access_key=settings.R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )
    return client
