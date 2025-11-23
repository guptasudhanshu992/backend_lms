from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_analytics_overview(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get overview statistics for API analytics
    
    Requires admin privileges
    """
    try:
        stats = await AnalyticsService.get_overview_stats(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics overview: {str(e)}")


@router.get("/endpoints")
async def get_endpoint_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get analytics grouped by endpoint
    
    Shows request counts, response times, success/error rates for each endpoint
    Requires admin privileges
    """
    try:
        stats = await AnalyticsService.get_endpoint_stats(
            db=db,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return {"endpoints": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch endpoint analytics: {str(e)}")


@router.get("/geography")
async def get_geographic_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get geographic distribution of API calls
    
    Shows request distribution by country and city
    Requires admin privileges
    """
    try:
        stats = await AnalyticsService.get_geographic_stats(
            db=db,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch geographic analytics: {str(e)}")


@router.get("/performance")
async def get_performance_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    interval: str = Query("hour", regex="^(hour|day|week)$", description="Time interval for grouping"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get performance metrics over time
    
    Shows request counts, response times, success/error rates over time
    Requires admin privileges
    """
    try:
        stats = await AnalyticsService.get_performance_timeline(
            db=db,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )
        return {"timeline": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch performance analytics: {str(e)}")


@router.get("/errors")
async def get_error_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get error analysis
    
    Shows error distribution by status code and endpoint
    Requires admin privileges
    """
    try:
        stats = await AnalyticsService.get_error_analysis(
            db=db,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch error analytics: {str(e)}")


@router.get("/slowest")
async def get_slowest_endpoints(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get slowest performing endpoints
    
    Shows endpoints with highest average and maximum response times
    Requires admin privileges
    """
    try:
        stats = await AnalyticsService.get_slowest_endpoints(
            db=db,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        return {"slowest_endpoints": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch slowest endpoints: {str(e)}")


@router.get("/stats/realtime")
async def get_realtime_stats(
    minutes: int = Query(5, ge=1, le=60, description="Number of minutes to look back"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get real-time statistics for the last N minutes
    
    Useful for monitoring current system performance
    Requires admin privileges
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(minutes=minutes)
        
        stats = await AnalyticsService.get_overview_stats(
            db=db,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Add real-time specific metrics
        stats["time_window_minutes"] = minutes
        stats["is_realtime"] = True
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch real-time stats: {str(e)}")


@router.get("/stats/comparison")
async def get_comparison_stats(
    period: str = Query("day", regex="^(hour|day|week|month)$", description="Comparison period"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get comparison statistics between current and previous period
    
    Useful for tracking trends and changes
    Requires admin privileges
    """
    try:
        # Calculate time periods
        end_date = datetime.utcnow()
        
        if period == "hour":
            delta = timedelta(hours=1)
        elif period == "day":
            delta = timedelta(days=1)
        elif period == "week":
            delta = timedelta(weeks=1)
        else:  # month
            delta = timedelta(days=30)
        
        current_start = end_date - delta
        previous_start = current_start - delta
        previous_end = current_start
        
        # Get stats for both periods
        current_stats = await AnalyticsService.get_overview_stats(
            db=db,
            start_date=current_start,
            end_date=end_date,
        )
        
        previous_stats = await AnalyticsService.get_overview_stats(
            db=db,
            start_date=previous_start,
            end_date=previous_end,
        )
        
        # Calculate changes
        def calculate_change(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return ((current - previous) / previous) * 100
        
        comparison = {
            "period": period,
            "current": current_stats,
            "previous": previous_stats,
            "changes": {
                "total_requests": calculate_change(
                    current_stats["total_requests"],
                    previous_stats["total_requests"]
                ),
                "avg_response_time": calculate_change(
                    current_stats["avg_response_time"],
                    previous_stats["avg_response_time"]
                ),
                "success_rate": current_stats["success_rate"] - previous_stats["success_rate"],
                "error_rate": current_stats["error_rate"] - previous_stats["error_rate"],
                "unique_users": calculate_change(
                    current_stats["unique_users"],
                    previous_stats["unique_users"]
                ),
            }
        }
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch comparison stats: {str(e)}")
