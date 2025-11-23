from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from datetime import datetime
from app.db.database import Base


class APIAnalytics(Base):
    """Model for tracking API requests and performance metrics"""
    __tablename__ = "api_analytics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Request Information
    endpoint = Column(String(500), nullable=False, index=True)
    method = Column(String(10), nullable=False, index=True)  # GET, POST, PUT, DELETE, etc.
    path = Column(String(500), nullable=False)
    query_params = Column(Text, nullable=True)  # JSON string of query parameters
    
    # Response Information
    status_code = Column(Integer, nullable=False, index=True)
    response_time = Column(Float, nullable=False)  # in milliseconds
    
    # User Information
    user_id = Column(Integer, nullable=True, index=True)  # No FK constraint - users table is SQLAlchemy Core
    # Note: User relationship not defined since users table uses SQLAlchemy Core
    
    # IP and Geolocation
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 max length
    city = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, index=True)
    country_code = Column(String(2), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Request/Response Data (for debugging)
    request_headers = Column(Text, nullable=True)  # JSON string
    request_body = Column(Text, nullable=True)  # JSON string (limited size)
    response_body = Column(Text, nullable=True)  # JSON string (limited size)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Additional metadata
    user_agent = Column(String(500), nullable=True)
    referer = Column(String(500), nullable=True)

    # Create composite indexes for common queries
    __table_args__ = (
        Index('idx_endpoint_method', 'endpoint', 'method'),
        Index('idx_endpoint_created', 'endpoint', 'created_at'),
        Index('idx_status_created', 'status_code', 'created_at'),
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_city_country', 'city', 'country'),
    )

    def __repr__(self):
        return f"<APIAnalytics {self.method} {self.endpoint} - {self.status_code} ({self.response_time}ms)>"
