import json
from app.services.d1_service import database
from app import models

__all__ = ['log']

def log(user_id: int | None, action: str, meta: dict | None = None, ip: str | None = None):
    # Convert meta dict to JSON string for SQLite compatibility
    meta_json = json.dumps(meta) if meta else json.dumps({})
    
    # Handle env-based admin (user_id 0 or "0") - set to None to avoid FK constraint
    if user_id == 0 or user_id == "0":
        user_id = None
    
    # Use ip_address as the column name (matches database schema)
    database.execute(models.audit_logs.insert().values(
        user_id=user_id, 
        action=action, 
        meta=meta_json, 
        ip_address=ip,
        status='success'
    ))
    return True
