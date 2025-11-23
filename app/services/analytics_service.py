from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import json
from app.orm_models.analytics import APIAnalytics


class AnalyticsService:
    """Service for API analytics operations"""

    @staticmethod
    async def log_api_call(
        db: Session,
        endpoint: str,
        method: str,
        path: str,
        status_code: int,
        response_time: float,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        city: Optional[str] = None,
        region: Optional[str] = None,
        country: Optional[str] = None,
        country_code: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        query_params: Optional[Dict] = None,
        request_headers: Optional[Dict] = None,
        request_body: Optional[Dict] = None,
        response_body: Optional[Dict] = None,
        error_message: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
    ) -> APIAnalytics:
        """Log an API call to the analytics database"""
        
        # Limit body sizes to prevent database bloat
        def truncate_json(data, max_length=5000):
            if data:
                json_str = json.dumps(data)
                return json_str[:max_length] if len(json_str) > max_length else json_str
            return None

        analytics_entry = APIAnalytics(
            endpoint=endpoint,
            method=method,
            path=path,
            query_params=json.dumps(query_params) if query_params else None,
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
            request_headers=truncate_json(request_headers),
            request_body=truncate_json(request_body),
            response_body=truncate_json(response_body),
            error_message=error_message,
            user_agent=user_agent,
            referer=referer,
        )
        
        db.add(analytics_entry)
        db.commit()
        db.refresh(analytics_entry)
        
        return analytics_entry

    @staticmethod
    async def get_overview_stats(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get overview statistics for API analytics"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        query = db.query(APIAnalytics).filter(
            APIAnalytics.created_at.between(start_date, end_date)
        )

        total_requests = query.count()
        avg_response_time = query.with_entities(
            func.avg(APIAnalytics.response_time)
        ).scalar() or 0

        # Success rate (2xx and 3xx status codes)
        successful_requests = query.filter(
            APIAnalytics.status_code.between(200, 399)
        ).count()
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0

        # Error rate (4xx and 5xx status codes)
        error_requests = query.filter(
            APIAnalytics.status_code >= 400
        ).count()
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0

        # Requests per minute (throughput)
        time_diff_minutes = (end_date - start_date).total_seconds() / 60
        requests_per_minute = total_requests / time_diff_minutes if time_diff_minutes > 0 else 0

        # Unique users
        unique_users = query.filter(
            APIAnalytics.user_id.isnot(None)
        ).with_entities(
            func.count(func.distinct(APIAnalytics.user_id))
        ).scalar() or 0

        # Unique IPs
        unique_ips = query.filter(
            APIAnalytics.ip_address.isnot(None)
        ).with_entities(
            func.count(func.distinct(APIAnalytics.ip_address))
        ).scalar() or 0

        return {
            "total_requests": total_requests,
            "avg_response_time": round(avg_response_time, 2),
            "success_rate": round(success_rate, 2),
            "error_rate": round(error_rate, 2),
            "requests_per_minute": round(requests_per_minute, 2),
            "unique_users": unique_users,
            "unique_ips": unique_ips,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    @staticmethod
    async def get_endpoint_stats(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get statistics grouped by endpoint"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        results = db.query(
            APIAnalytics.endpoint,
            APIAnalytics.method,
            func.count(APIAnalytics.id).label('request_count'),
            func.avg(APIAnalytics.response_time).label('avg_response_time'),
            func.min(APIAnalytics.response_time).label('min_response_time'),
            func.max(APIAnalytics.response_time).label('max_response_time'),
            func.sum(
                func.case((APIAnalytics.status_code.between(200, 399), 1), else_=0)
            ).label('success_count'),
            func.sum(
                func.case((APIAnalytics.status_code >= 400, 1), else_=0)
            ).label('error_count'),
        ).filter(
            APIAnalytics.created_at.between(start_date, end_date)
        ).group_by(
            APIAnalytics.endpoint,
            APIAnalytics.method
        ).order_by(
            desc('request_count')
        ).limit(limit).all()

        return [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "request_count": r.request_count,
                "avg_response_time": round(r.avg_response_time, 2),
                "min_response_time": round(r.min_response_time, 2),
                "max_response_time": round(r.max_response_time, 2),
                "success_count": r.success_count,
                "error_count": r.error_count,
                "success_rate": round(
                    (r.success_count / r.request_count * 100) if r.request_count > 0 else 0,
                    2
                ),
            }
            for r in results
        ]

    @staticmethod
    async def get_geographic_stats(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get geographic distribution of API calls"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # Country-level stats
        country_results = db.query(
            APIAnalytics.country,
            APIAnalytics.country_code,
            func.count(APIAnalytics.id).label('request_count'),
            func.avg(APIAnalytics.response_time).label('avg_response_time'),
        ).filter(
            and_(
                APIAnalytics.created_at.between(start_date, end_date),
                APIAnalytics.country.isnot(None)
            )
        ).group_by(
            APIAnalytics.country,
            APIAnalytics.country_code
        ).order_by(
            desc('request_count')
        ).limit(limit).all()

        # City-level stats
        city_results = db.query(
            APIAnalytics.city,
            APIAnalytics.region,
            APIAnalytics.country,
            APIAnalytics.latitude,
            APIAnalytics.longitude,
            func.count(APIAnalytics.id).label('request_count'),
            func.avg(APIAnalytics.response_time).label('avg_response_time'),
        ).filter(
            and_(
                APIAnalytics.created_at.between(start_date, end_date),
                APIAnalytics.city.isnot(None)
            )
        ).group_by(
            APIAnalytics.city,
            APIAnalytics.region,
            APIAnalytics.country,
            APIAnalytics.latitude,
            APIAnalytics.longitude
        ).order_by(
            desc('request_count')
        ).limit(limit).all()

        return {
            "countries": [
                {
                    "country": r.country,
                    "country_code": r.country_code,
                    "request_count": r.request_count,
                    "avg_response_time": round(r.avg_response_time, 2),
                }
                for r in country_results
            ],
            "cities": [
                {
                    "city": r.city,
                    "region": r.region,
                    "country": r.country,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "request_count": r.request_count,
                    "avg_response_time": round(r.avg_response_time, 2),
                }
                for r in city_results
            ],
        }

    @staticmethod
    async def get_performance_timeline(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        interval: str = "hour",  # hour, day, week
    ) -> List[Dict[str, Any]]:
        """Get performance metrics over time"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # Determine time bucket based on interval
        if interval == "hour":
            time_format = func.date_trunc('hour', APIAnalytics.created_at)
        elif interval == "day":
            time_format = func.date_trunc('day', APIAnalytics.created_at)
        else:  # week
            time_format = func.date_trunc('week', APIAnalytics.created_at)

        results = db.query(
            time_format.label('time_bucket'),
            func.count(APIAnalytics.id).label('request_count'),
            func.avg(APIAnalytics.response_time).label('avg_response_time'),
            func.sum(
                func.case((APIAnalytics.status_code.between(200, 399), 1), else_=0)
            ).label('success_count'),
            func.sum(
                func.case((APIAnalytics.status_code >= 400, 1), else_=0)
            ).label('error_count'),
        ).filter(
            APIAnalytics.created_at.between(start_date, end_date)
        ).group_by(
            'time_bucket'
        ).order_by(
            'time_bucket'
        ).all()

        return [
            {
                "timestamp": r.time_bucket.isoformat(),
                "request_count": r.request_count,
                "avg_response_time": round(r.avg_response_time, 2),
                "success_count": r.success_count,
                "error_count": r.error_count,
                "error_rate": round(
                    (r.error_count / r.request_count * 100) if r.request_count > 0 else 0,
                    2
                ),
            }
            for r in results
        ]

    @staticmethod
    async def get_error_analysis(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Analyze errors and their distribution"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        # Errors by status code
        status_results = db.query(
            APIAnalytics.status_code,
            func.count(APIAnalytics.id).label('count'),
        ).filter(
            and_(
                APIAnalytics.created_at.between(start_date, end_date),
                APIAnalytics.status_code >= 400
            )
        ).group_by(
            APIAnalytics.status_code
        ).order_by(
            desc('count')
        ).all()

        # Errors by endpoint
        endpoint_results = db.query(
            APIAnalytics.endpoint,
            APIAnalytics.method,
            APIAnalytics.status_code,
            func.count(APIAnalytics.id).label('count'),
        ).filter(
            and_(
                APIAnalytics.created_at.between(start_date, end_date),
                APIAnalytics.status_code >= 400
            )
        ).group_by(
            APIAnalytics.endpoint,
            APIAnalytics.method,
            APIAnalytics.status_code
        ).order_by(
            desc('count')
        ).limit(limit).all()

        # Recent errors with details
        recent_errors = db.query(APIAnalytics).filter(
            and_(
                APIAnalytics.created_at.between(start_date, end_date),
                APIAnalytics.status_code >= 400
            )
        ).order_by(
            desc(APIAnalytics.created_at)
        ).limit(20).all()

        return {
            "by_status_code": [
                {
                    "status_code": r.status_code,
                    "count": r.count,
                }
                for r in status_results
            ],
            "by_endpoint": [
                {
                    "endpoint": r.endpoint,
                    "method": r.method,
                    "status_code": r.status_code,
                    "count": r.count,
                }
                for r in endpoint_results
            ],
            "recent_errors": [
                {
                    "id": e.id,
                    "endpoint": e.endpoint,
                    "method": e.method,
                    "status_code": e.status_code,
                    "error_message": e.error_message,
                    "user_id": e.user_id,
                    "ip_address": e.ip_address,
                    "created_at": e.created_at.isoformat(),
                }
                for e in recent_errors
            ],
        }

    @staticmethod
    async def get_slowest_endpoints(
        db: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get the slowest performing endpoints"""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        results = db.query(
            APIAnalytics.endpoint,
            APIAnalytics.method,
            func.avg(APIAnalytics.response_time).label('avg_response_time'),
            func.max(APIAnalytics.response_time).label('max_response_time'),
            func.count(APIAnalytics.id).label('request_count'),
        ).filter(
            APIAnalytics.created_at.between(start_date, end_date)
        ).group_by(
            APIAnalytics.endpoint,
            APIAnalytics.method
        ).order_by(
            desc('avg_response_time')
        ).limit(limit).all()

        return [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "avg_response_time": round(r.avg_response_time, 2),
                "max_response_time": round(r.max_response_time, 2),
                "request_count": r.request_count,
            }
            for r in results
        ]
