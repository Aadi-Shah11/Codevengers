"""
Access logs and monitoring router
Enhanced with comprehensive logging service integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from database.connection import get_db
from services.logging_service import LoggingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/")
async def get_access_logs(
    limit: int = Query(50, ge=1, le=500, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    gate_id: Optional[str] = Query(None, description="Filter by gate ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    license_plate: Optional[str] = Query(None, description="Filter by license plate"),
    access_granted: Optional[bool] = Query(None, description="Filter by access result"),
    verification_method: Optional[str] = Query(None, regex="^(id_only|vehicle_only|both)$"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    search: Optional[str] = Query(None, description="Search term for logs"),
    db: Session = Depends(get_db)
):
    """
    Get access logs with comprehensive filtering and pagination
    
    This endpoint provides access to the complete audit trail with:
    - Multiple filtering options (gate, user, vehicle, date range, etc.)
    - Full-text search across log content
    - Pagination for large result sets
    - Enhanced log data with security assessments
    - Related alert information
    
    Returns detailed log information including user/vehicle details,
    security assessments, and related alerts.
    """
    try:
        logger.info(f"Access logs request: limit={limit}, offset={offset}, filters={locals()}")
        
        logging_service = LoggingService(db)
        
        # Prepare filters
        filters = {}
        if gate_id:
            filters["gate_id"] = gate_id
        if user_id:
            filters["user_id"] = user_id.upper()
        if license_plate:
            filters["license_plate"] = license_plate.upper()
        if access_granted is not None:
            filters["access_granted"] = access_granted
        if verification_method:
            filters["verification_method"] = verification_method
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        if search:
            filters["search"] = search
        
        # Prepare pagination
        pagination = {
            "limit": limit,
            "offset": offset
        }
        
        # Get logs using logging service
        result = logging_service.get_access_logs(filters, pagination)
        
        if result["success"]:
            logger.info(f"Retrieved {len(result['logs'])} access logs")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access logs: {str(e)}"
        )

@router.get("/recent")
async def get_recent_logs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get most recent access logs
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        logs = access_repo.get_recent_logs(limit=limit)
        
        return {
            "logs": [log.to_dict() for log in logs],
            "total": len(logs),
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent logs: {str(e)}"
        )

@router.get("/denied")
async def get_denied_access_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get access logs where access was denied
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        logs = access_repo.get_denied_access_logs(limit=limit, skip=offset)
        
        return {
            "logs": [log.to_dict() for log in logs],
            "total": len(logs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get denied access logs: {str(e)}"
        )

@router.get("/statistics")
async def get_access_statistics(
    days: int = Query(7, ge=1, le=365),
    gate_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get access statistics for specified period
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        stats = access_repo.get_access_statistics(days=days, gate_id=gate_id)
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access statistics: {str(e)}"
        )

@router.get("/patterns/hourly")
async def get_hourly_patterns(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get hourly access patterns for analytics
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        patterns = access_repo.get_hourly_access_pattern(days=days)
        
        return {
            "patterns": patterns,
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hourly patterns: {str(e)}"
        )

@router.get("/patterns/daily")
async def get_daily_patterns(
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Get daily access statistics for trends
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        patterns = access_repo.get_daily_statistics(days=days)
        
        return {
            "patterns": patterns,
            "period_days": days
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily patterns: {str(e)}"
        )

@router.get("/search")
async def search_logs(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Search access logs by user ID, license plate, or notes
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        logs = access_repo.search_logs(q, limit=limit, skip=offset)
        
        return {
            "logs": [log.to_dict() for log in logs],
            "total": len(logs),
            "limit": limit,
            "offset": offset,
            "search_term": q
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}"
        )

@router.get("/{log_id}")
async def get_log_by_id(
    log_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific access log by ID
    """
    try:
        db_service = DatabaseService(db)
        access_repo = db_service.access_log_repo
        
        log = access_repo.get_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access log not found"
            )
        
        return log.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access log: {str(e)}"
        )@
router.post("/")
async def create_access_log(
    gate_id: str = Query(..., description="Gate identifier"),
    user_id: Optional[str] = Query(None, description="User ID"),
    license_plate: Optional[str] = Query(None, description="License plate"),
    access_granted: bool = Query(..., description="Whether access was granted"),
    notes: Optional[str] = Query(None, description="Additional notes"),
    db: Session = Depends(get_db)
):
    """
    Create a new access log entry
    
    This endpoint allows manual creation of access log entries for
    testing, integration, or administrative purposes.
    """
    try:
        if not user_id and not license_plate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either user_id or license_plate"
            )
        
        logging_service = LoggingService(db)
        
        # Additional data for enhanced logging
        additional_data = {
            "source": "manual_entry",
            "created_via": "api"
        }
        
        result = logging_service.log_access_attempt(
            gate_id=gate_id,
            user_id=user_id.upper() if user_id else None,
            license_plate=license_plate.upper() if license_plate else None,
            access_granted=access_granted,
            notes=notes,
            additional_data=additional_data
        )
        
        if result["success"]:
            logger.info(f"Manual access log created: {result['log_id']}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create access log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create access log: {str(e)}"
        )

@router.get("/statistics")
async def get_access_statistics(
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    gate_id: Optional[str] = Query(None, description="Filter by gate ID"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive access statistics and analytics
    
    Returns detailed statistics including:
    - Basic access metrics (total, granted, denied)
    - Hourly and daily patterns
    - Verification method breakdown
    - Security metrics and threat assessment
    - Top users and vehicles by access frequency
    """
    try:
        logging_service = LoggingService(db)
        
        result = logging_service.get_access_statistics(days, gate_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access statistics: {str(e)}"
        )

@router.get("/audit/{entity_type}/{entity_id}")
async def get_audit_trail(
    entity_type: str = Query(..., regex="^(user|vehicle)$", description="Type of entity"),
    entity_id: str = Query(..., description="Entity identifier"),
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive audit trail for a specific user or vehicle
    
    Returns chronological audit trail including:
    - All access attempts
    - Security alerts
    - Administrative actions
    - Summary statistics
    """
    try:
        logging_service = LoggingService(db)
        
        result = logging_service.get_audit_trail(entity_type, entity_id.upper(), days)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit trail: {str(e)}"
        )

@router.get("/export")
async def export_logs(
    format_type: str = Query("json", regex="^(json|csv)$", description="Export format"),
    gate_id: Optional[str] = Query(None, description="Filter by gate ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    license_plate: Optional[str] = Query(None, description="Filter by license plate"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Export access logs in JSON or CSV format
    
    Supports the same filtering options as the main logs endpoint.
    Returns formatted data suitable for download or external processing.
    """
    try:
        logging_service = LoggingService(db)
        
        # Prepare filters
        filters = {}
        if gate_id:
            filters["gate_id"] = gate_id
        if user_id:
            filters["user_id"] = user_id.upper()
        if license_plate:
            filters["license_plate"] = license_plate.upper()
        if start_date:
            filters["start_date"] = start_date
        if end_date:
            filters["end_date"] = end_date
        
        result = logging_service.export_logs(filters, format_type)
        
        if result["success"]:
            # Set appropriate content type
            if format_type == "csv":
                media_type = "text/csv"
            else:
                media_type = "application/json"
            
            return Response(
                content=result["data"] if format_type == "csv" else str(result["data"]),
                media_type=media_type,
                headers={
                    "Content-Disposition": f"attachment; filename={result['filename']}"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export logs: {str(e)}"
        )

@router.delete("/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=30, le=365, description="Number of days to keep"),
    confirm: bool = Query(False, description="Confirmation flag"),
    db: Session = Depends(get_db)
):
    """
    Clean up old access logs and resolved alerts
    
    This is a maintenance operation that removes old data to manage
    database size. Requires explicit confirmation.
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cleanup operation requires confirmation. Set confirm=true"
            )
        
        logging_service = LoggingService(db)
        
        result = logging_service.cleanup_old_logs(days_to_keep)
        
        if result["success"]:
            logger.info(f"Cleanup completed: {result['deleted_logs']} logs, {result['deleted_alerts']} alerts")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cleanup logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup logs: {str(e)}"
        )

@router.get("/recent")
async def get_recent_logs(
    limit: int = Query(20, ge=1, le=100, description="Number of recent logs"),
    include_security_assessment: bool = Query(True, description="Include security assessment"),
    db: Session = Depends(get_db)
):
    """
    Get most recent access logs with optional security assessment
    
    Optimized endpoint for real-time monitoring and dashboard displays.
    """
    try:
        logging_service = LoggingService(db)
        
        filters = {}
        pagination = {"limit": limit, "offset": 0}
        
        result = logging_service.get_access_logs(filters, pagination)
        
        if result["success"]:
            # Optionally remove security assessment for faster response
            if not include_security_assessment:
                for log in result["logs"]:
                    log.pop("security_assessment", None)
                    log.pop("related_alerts", None)
            
            return {
                "logs": result["logs"],
                "total": result["total"],
                "limit": limit,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recent logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent logs: {str(e)}"
        )

@router.get("/denied")
async def get_denied_access_logs(
    limit: int = Query(50, ge=1, le=200, description="Number of denied logs"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """
    Get access logs where access was denied
    
    Specialized endpoint for security monitoring and threat analysis.
    """
    try:
        logging_service = LoggingService(db)
        
        filters = {
            "access_granted": False,
            "start_date": (datetime.now() - timedelta(days=days)).isoformat(),
            "end_date": datetime.now().isoformat()
        }
        pagination = {"limit": limit, "offset": offset}
        
        result = logging_service.get_access_logs(filters, pagination)
        
        if result["success"]:
            return {
                "logs": result["logs"],
                "total": result["total"],
                "limit": limit,
                "offset": offset,
                "days": days
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get denied access logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get denied access logs: {str(e)}"
        )

@router.get("/patterns/hourly")
async def get_hourly_patterns(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    gate_id: Optional[str] = Query(None, description="Filter by gate ID"),
    db: Session = Depends(get_db)
):
    """
    Get hourly access patterns for analytics and capacity planning
    """
    try:
        logging_service = LoggingService(db)
        
        result = logging_service.get_access_statistics(days, gate_id)
        
        if result["success"]:
            return {
                "patterns": result["hourly_patterns"],
                "period_days": days,
                "gate_id": gate_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hourly patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hourly patterns: {str(e)}"
        )

@router.get("/patterns/daily")
async def get_daily_patterns(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    gate_id: Optional[str] = Query(None, description="Filter by gate ID"),
    db: Session = Depends(get_db)
):
    """
    Get daily access statistics for trend analysis
    """
    try:
        logging_service = LoggingService(db)
        
        result = logging_service.get_access_statistics(days, gate_id)
        
        if result["success"]:
            return {
                "patterns": result["daily_statistics"],
                "period_days": days,
                "gate_id": gate_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get daily patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily patterns: {str(e)}"
        )

@router.get("/search")
async def search_logs(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    db: Session = Depends(get_db)
):
    """
    Search access logs by user ID, license plate, notes, or other content
    
    Performs full-text search across log content with relevance ranking.
    """
    try:
        logging_service = LoggingService(db)
        
        filters = {"search": q}
        pagination = {"limit": limit, "offset": offset}
        
        result = logging_service.get_access_logs(filters, pagination)
        
        if result["success"]:
            return {
                "logs": result["logs"],
                "total": result["total"],
                "limit": limit,
                "offset": offset,
                "search_term": q
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}"
        )

@router.get("/{log_id}")
async def get_log_by_id(
    log_id: int,
    include_related: bool = Query(True, description="Include related alerts and context"),
    db: Session = Depends(get_db)
):
    """
    Get specific access log by ID with optional related information
    """
    try:
        logging_service = LoggingService(db)
        
        log = logging_service.access_log_repo.get_by_id(log_id)
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Access log not found"
            )
        
        log_dict = log.to_dict()
        
        if include_related:
            # Add enhanced information
            log_dict["security_assessment"] = logging_service._assess_log_security(log)
            log_dict["related_alerts"] = logging_service._get_related_alerts(log)
        
        return {
            "log": log_dict,
            "include_related": include_related
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get access log {log_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get access log: {str(e)}"
        )