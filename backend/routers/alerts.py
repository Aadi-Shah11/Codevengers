"""
Security alerts router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from database.connection import get_db
from services.database_service import DatabaseService

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.get("/")
async def get_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    active_only: bool = Query(True),
    alert_type: Optional[str] = None,
    gate_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get security alerts with filtering and pagination
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        # Get alerts based on filters
        if alert_type:
            from models.alert import AlertType
            try:
                type_enum = AlertType(alert_type.lower())
                alerts = alert_repo.get_alerts_by_type(type_enum, limit=limit, skip=offset)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid alert type: {alert_type}"
                )
        elif gate_id:
            alerts = alert_repo.get_alerts_by_gate(gate_id, limit=limit, skip=offset)
        elif active_only:
            alerts = alert_repo.get_active_alerts(limit=limit, skip=offset)
        else:
            alerts = alert_repo.get_all(skip=offset, limit=limit)
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts),
            "limit": limit,
            "offset": offset,
            "filters": {
                "active_only": active_only,
                "alert_type": alert_type,
                "gate_id": gate_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )

@router.get("/recent")
async def get_recent_alerts(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recent alerts within specified hours
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        alerts = alert_repo.get_recent_alerts(hours=hours, limit=limit)
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts),
            "hours": hours,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent alerts: {str(e)}"
        )

@router.get("/active")
async def get_active_alerts(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all active (unresolved) alerts
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        alerts = alert_repo.get_active_alerts(limit=limit)
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts),
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active alerts: {str(e)}"
        )

@router.get("/critical")
async def get_critical_alerts(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get most critical active alerts
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        alerts = alert_repo.get_critical_alerts(limit=limit)
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts),
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get critical alerts: {str(e)}"
        )

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Resolve an active alert
    """
    try:
        db_service = DatabaseService(db)
        result = db_service.resolve_alert(alert_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}"
        )

@router.post("/resolve/user/{user_id}")
async def resolve_user_alerts(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Resolve all alerts for a specific user
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        resolved_count = alert_repo.resolve_alerts_by_user(user_id)
        
        return {
            "success": True,
            "message": f"Resolved {resolved_count} alerts for user {user_id}",
            "user_id": user_id,
            "resolved_count": resolved_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve user alerts: {str(e)}"
        )

@router.post("/resolve/vehicle/{license_plate}")
async def resolve_vehicle_alerts(
    license_plate: str,
    db: Session = Depends(get_db)
):
    """
    Resolve all alerts for a specific vehicle
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        resolved_count = alert_repo.resolve_alerts_by_vehicle(license_plate.upper())
        
        return {
            "success": True,
            "message": f"Resolved {resolved_count} alerts for vehicle {license_plate.upper()}",
            "license_plate": license_plate.upper(),
            "resolved_count": resolved_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve vehicle alerts: {str(e)}"
        )

@router.get("/statistics")
async def get_alert_statistics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get alert statistics for specified period
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        stats = alert_repo.get_alert_statistics(days=days)
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert statistics: {str(e)}"
        )

@router.get("/trends")
async def get_alert_trends(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Get daily alert trends for analytics
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        trends = alert_repo.get_alert_trends(days=days)
        
        return {
            "trends": trends,
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert trends: {str(e)}"
        )

@router.get("/search")
async def search_alerts(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Search alerts by message, user ID, or license plate
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        alerts = alert_repo.search_alerts(q, limit=limit, skip=offset)
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total": len(alerts),
            "limit": limit,
            "offset": offset,
            "search_term": q
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search alerts: {str(e)}"
        )

@router.get("/{alert_id}")
async def get_alert_by_id(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific alert by ID
    """
    try:
        db_service = DatabaseService(db)
        alert_repo = db_service.alert_repo
        
        alert = alert_repo.get_by_id(alert_id)
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return alert.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert: {str(e)}"
        )