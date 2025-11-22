from app.services.d1_service import database
from app import models

def create_session(user_id: int, user_agent: str = None, ip: str = None):
    res = database.execute(models.sessions.insert().values(user_id=user_id, user_agent=user_agent, ip=ip))
    return res


def list_sessions(user_id: int):
    return database.fetch_all(models.sessions.select().where(models.sessions.c.user_id == user_id).order_by(models.sessions.c.created_at.desc()))


def revoke_session(session_id: int):
    database.execute(models.sessions.update().where(models.sessions.c.id == session_id).values(revoked=True))
    return True
