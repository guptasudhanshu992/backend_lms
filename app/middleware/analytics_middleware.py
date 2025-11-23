import time
import json
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session
from app.database import get_session_local
from app.services.analytics_service import AnalyticsService
import logging
import asyncio

logger = logging.getLogger(__name__)


class APIAnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically track all API requests"""
    
    # Endpoints to exclude from analytics (to prevent noise)
    EXCLUDED_PATHS = {
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
        "/health",
        "/metrics",
    }
    
    # Endpoints that should capture detailed IP/geo information
    TRACK_GEOLOCATION_PATHS = {
        "/api/auth/",
        "/api/courses/",
        "/api/payments/",
        "/api/enrollment/",
    }

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.geolocation_service = None
        try:
            from app.services.geolocation_service import GeolocationService
            self.geolocation_service = GeolocationService()
        except Exception as e:
            logger.warning(f"Geolocation service not available: {e}")

    async def dispatch(self, request: Request, call_next):
        """Process each request and log analytics"""
        
        # Skip excluded paths
        if any(request.url.path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Start timing
        start_time = time.time()
        
        # Extract request information
        method = request.method
        path = request.url.path
        endpoint = self._normalize_endpoint(path)
        
        # Get client IP
        ip_address = self._get_client_ip(request)
        
        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        
        # Capture geolocation if needed
        city = None
        region = None
        country = None
        country_code = None
        latitude = None
        longitude = None
        
        should_track_geo = any(
            path.startswith(geo_path) for geo_path in self.TRACK_GEOLOCATION_PATHS
        )
        
        if should_track_geo and self.geolocation_service and ip_address:
            try:
                geo_data = await self.geolocation_service.get_location(ip_address)
                if geo_data:
                    city = geo_data.get("city")
                    region = geo_data.get("region")
                    country = geo_data.get("country")
                    country_code = geo_data.get("country_code")
                    latitude = geo_data.get("latitude")
                    longitude = geo_data.get("longitude")
            except Exception as e:
                logger.debug(f"Geolocation lookup failed for {ip_address}: {e}")
        
        # Get query parameters
        query_params = dict(request.query_params) if request.query_params else None
        
        # Get headers (filter sensitive ones)
        request_headers = self._filter_headers(dict(request.headers))
        user_agent = request.headers.get("user-agent")
        referer = request.headers.get("referer")
        
        # Capture request body for POST/PUT/PATCH (with size limit)
        request_body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body without consuming it
                body_bytes = await request.body()
                if len(body_bytes) < 10000:  # Only capture if less than 10KB
                    request_body = json.loads(body_bytes) if body_bytes else None
            except Exception:
                pass
        
        # Process request
        response = None
        status_code = 500
        error_message = None
        response_body = None
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Try to capture response body for errors (with size limit)
            if status_code >= 400:
                try:
                    response_body_bytes = b""
                    async for chunk in response.body_iterator:
                        response_body_bytes += chunk
                        if len(response_body_bytes) > 5000:  # Max 5KB for errors
                            break
                    
                    if response_body_bytes:
                        response_body = json.loads(response_body_bytes)
                        error_message = response_body.get("detail") or response_body.get("message")
                    
                    # Recreate response with the consumed body
                    response = Response(
                        content=response_body_bytes,
                        status_code=status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )
                except Exception:
                    pass
                    
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            status_code = 500
            error_message = str(e)
            raise
        finally:
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log to database asynchronously
            asyncio.create_task(
                self._log_analytics(
                    endpoint=endpoint,
                    method=method,
                    path=path,
                    status_code=status_code,
                    response_time=response_time,
                    user_id=user_id,
                    ip_address=ip_address,
                    city=city,
                    region=region,
                    country=country,
                    country_code=country_code,
                    latitude=latitude,
                    longitude=longitude,
                    query_params=query_params,
                    request_headers=request_headers,
                    request_body=request_body,
                    response_body=response_body,
                    error_message=error_message,
                    user_agent=user_agent,
                    referer=referer,
                )
            )
        
        return response

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path by removing IDs and dynamic segments"""
        parts = path.split("/")
        normalized_parts = []
        
        for part in parts:
            if not part:
                continue
            # Replace numeric IDs with placeholder
            if part.isdigit():
                normalized_parts.append("{id}")
            # Replace UUIDs with placeholder
            elif len(part) == 36 and part.count("-") == 4:
                normalized_parts.append("{uuid}")
            else:
                normalized_parts.append(part)
        
        return "/" + "/".join(normalized_parts)

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Extract client IP address from request"""
        # Check for forwarded IP first (if behind proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return None

    def _filter_headers(self, headers: dict) -> dict:
        """Filter out sensitive headers"""
        sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
        }
        
        return {
            k: v for k, v in headers.items()
            if k.lower() not in sensitive_headers
        }

    async def _log_analytics(self, **kwargs):
        """Log analytics data to database"""
        SessionLocal = get_session_local()
        if SessionLocal is None:
            logger.warning("SessionLocal not initialized, skipping analytics logging")
            return
        
        db: Session = SessionLocal()
        try:
            await AnalyticsService.log_api_call(db, **kwargs)
        except Exception as e:
            logger.error(f"Failed to log analytics: {e}")
        finally:
            db.close()
