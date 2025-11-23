"""
Database module - Re-exports from app.db.database for backwards compatibility
"""
from app.db.database import Base, get_db, init_db

# Lazy load SessionLocal
def get_session_local():
    from app.db.database import SessionLocal
    if SessionLocal is None:
        init_db()
    return SessionLocal

SessionLocal = None  # Will be initialized when needed

__all__ = ['Base', 'SessionLocal', 'get_db', 'init_db', 'get_session_local']
