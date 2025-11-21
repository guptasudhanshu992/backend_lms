import uuid
from typing import Tuple
from app.utils.s3_client import create_r2_client
from app.config.settings import settings


def upload_fileobj(fileobj, filename: str = None) -> Tuple[str, str]:
    """Upload file-like object to R2 and return (key, url)

    Assumes `settings.R2_BUCKET` is set.
    """
    # create client lazily so module import doesn't fail when R2 is not configured
    client = create_r2_client()
    if client is None:
        raise RuntimeError("R2 client not configured. Set R2_ENDPOINT, R2_ACCESS_KEY, and R2_SECRET_KEY.")

    key = f"uploads/{uuid.uuid4().hex}_{filename or 'file'}"
    client.put_object(Bucket=settings.R2_BUCKET, Key=key, Body=fileobj)
    # Construct a public URL using the R2 endpoint; users may need custom domain
    url = f"{settings.R2_ENDPOINT}/{settings.R2_BUCKET}/{key}"
    return key, url


def download_fileobj(key: str):
    from app.config.settings import settings

    client = create_r2_client()
    if client is None:
        raise RuntimeError("R2 client not configured. Set R2_ENDPOINT, R2_ACCESS_KEY, and R2_SECRET_KEY.")

    resp = client.get_object(Bucket=settings.R2_BUCKET, Key=key)
    return resp["Body"].read()
