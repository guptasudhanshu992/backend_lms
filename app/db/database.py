"""
Database configuration for SQLAlchemy ORM models
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

# Create declarative base for ORM models (doesn't require DB connection)
Base = declarative_base()

# Engine and session factory (lazy initialization)
engine = None
SessionLocal = None


def init_db():
    """Initialize database engine and session factory"""
    global engine, SessionLocal
    
    if engine is not None:
        return engine
    
    # Create engine
    SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
    
    # Handle SQLite URLs
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine = create_engine(
            SQLALCHEMY_DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
    else:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine


# Dependency for FastAPI routes
def get_db():
    """Get database session"""
    if SessionLocal is None:
        init_db()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
