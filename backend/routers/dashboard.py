"""
Dashboard and analytics router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from database.connection import get_db
from services.database_service import DatabaseService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/")
async def get_dashboard_data(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for the specified period
    """
    try:
        db_service = DatabaseService(db)
        dashboard_data = db_service.get_dashboard_data(days=days)
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )

@router.get("/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db)
):
    """
    Get quick dashboard summary for today
    """
    try:
        db_service = DatabaseService(db)
        
        # Get today's statistics
        today_stats = db_service.get_dashboard_data(days=1)
        
        # Get system health
        system_health = db_service.get_system_health()
        
        # Get critical alerts
        alert_repo = db_service.alert_repo
        critical_alerts = alert_repo.get_critical_alerts(limit=5)
        
        summary = {
            "system_status": system_health["status"],
            "today_access_attempts": today_stats["access_statistics"]["total_attempts"],
            "today_success_rate": today_stats["access_statistics"]["success_rate"],
            "active_alerts": len(today_stats["active_alerts"]),
            "critical_alerts": len(critical_alerts),
            "total_users": today_stats["user_statistics"]["total_users"],
            "total_vehicles": today_stats["vehicle_statistics"]["total_vehicles"],
            "last_updated": today_stats["access_statistics"].get("period_days", 1)
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard summary: {str(e)}"
        )

@router.get("/analytics")
async def get_analytics_data(
    period: str = Query("week", regex="^(day|week|month)$"),
    db: Session = Depends(get_db)
):
    """
    Get analytics data for different time periods
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        alert_repo = db_service.alert_repo
        
        # Determine days based on period
        days_map = {"day": 1, "week": 7, "month": 30}
        days = days_map[period]
        
        # Get access statistics
        access_stats = access_repo.get_access_statistics(days=days)
        
        # Get alert statistics
        alert_stats = alert_repo.get_alert_statistics(days=days)
        
        # Get patterns
        if period == "day":
            patterns = access_repo.get_hourly_access_pattern(days=1)
            pattern_type = "hourly"
        else:
            patterns = access_repo.get_daily_statistics(days=days)
            pattern_type = "daily"
        
        analytics = {
            "period": period,
            "days": days,
            "access_statistics": access_stats,
            "alert_statistics": alert_stats,
            "patterns": {
                "type": pattern_type,
                "data": patterns
            }
        }
        
        return analytics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics data: {str(e)}"
        )

@router.get("/live")
async def get_live_data(
    db: Session = Depends(get_db)
):
    """
    Get live dashboard data (last hour activity)
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        alert_repo = db_service.alert_repo
        
        # Get recent logs (last hour)
        recent_logs = access_repo.get_recent_logs(limit=20)
        
        # Get recent alerts (last hour)
        recent_alerts = alert_repo.get_recent_alerts(hours=1, limit=10)
        
        # Get active alerts
        active_alerts = alert_repo.get_active_alerts(limit=10)
        
        live_data = {
            "timestamp": access_repo.db.execute("SELECT NOW()").scalar().isoformat(),
            "recent_activity": {
                "logs": [log.to_dict() for log in recent_logs[:10]],
                "alerts": [alert.to_dict() for alert in recent_alerts]
            },
            "active_alerts": [alert.to_dict() for alert in active_alerts],
            "counts": {
                "recent_logs": len(recent_logs),
                "recent_alerts": len(recent_alerts),
                "active_alerts": len(active_alerts)
            }
        }
        
        return live_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get live data: {str(e)}"
        )

@router.get("/gates")
async def get_gate_statistics(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get statistics by gate for the specified period
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        # Get all gates from recent logs
        recent_logs = access_repo.get_recent_logs(limit=1000)
        gates = list(set(log.gate_id for log in recent_logs if log.gate_id))
        
        gate_stats = {}
        for gate_id in gates:
            stats = access_repo.get_access_statistics(days=days, gate_id=gate_id)
            gate_stats[gate_id] = stats
        
        return {
            "period_days": days,
            "gates": gate_stats,
            "total_gates": len(gates)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gate statistics: {str(e)}"
        )

@router.get("/search")
async def search_dashboard_data(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Search across all dashboard data
    """
    try:
        db_service = DatabaseService(db)
        search_results = db_service.search_data(q, limit=50)
        
        return search_results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search dashboard data: {str(e)}"
        )