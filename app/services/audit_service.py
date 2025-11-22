import json
from app.services.d1_service import database
from app import models

async def log(user_id: int | None, action: str, meta: dict | None = None, ip: str | None = None):
    # Convert meta dict to JSON string for SQLite compatibility
    meta_json = json.dumps(meta) if meta else json.dumps({})
    await database.execute(models.audit_logs.insert().values(user_id=user_id, action=action, meta=meta_json, ip=ip))
    return True
