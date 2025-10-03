"""
Authentication and authorization router
Enhanced with comprehensive ID verification logic
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from database.connection import get_db
from services.verification_service import VerificationService
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

class IDVerificationRequest(BaseModel):
    id_number: str = Field(..., min_length=1, max_length=20, description="User ID to verify")
    scan_method: str = Field(default="manual", regex="^(qr|barcode|manual)$", description="Method used to scan ID")

class IDVerificationResponse(BaseModel):
    access_granted: bool
    user_id: str
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    verification_method: str
    timestamp: str
    message: str
    security_level: Optional[str] = None

@router.post("/verify_id", response_model=Dict[str, Any])
async def verify_id(
    request: IDVerificationRequest,
    gate_id: str = Query(default="MAIN_GATE", description="Gate identifier"),
    db: Session = Depends(get_db)
):
    """
    Verify user ID against database with comprehensive validation
    
    This is the core endpoint for ID-based access control. It performs:
    - Input validation and sanitization
    - User lookup and status verification
    - Security checks (suspicious patterns, rate limiting)
    - Access logging and alert generation
    - Comprehensive response formatting
    
    Returns detailed verification results including user information,
    access decision, and security metadata.
    """
    try:
        logger.info(f"ID verification request: {request.id_number} via {request.scan_method} at {gate_id}")
        
        verification_service = VerificationService(db)
        
        # Perform comprehensive access verification
        result = verification_service.perform_access_verification(
            user_id=request.id_number,
            gate_id=gate_id,
            scan_method=request.scan_method
        )
        
        # Extract user verification details
        user_verification = result.get("user_verification", {})
        
        # Format response for API consumers
        response = {
            "access_granted": result["access_granted"],
            "user_id": request.id_number,
            "user_name": user_verification.get("user_name"),
            "user_role": user_verification.get("user_role"),
            "user_department": user_verification.get("user_department"),
            "user_status": user_verification.get("user_status"),
            "verification_method": result["verification_method"],
            "timestamp": result["timestamp"],
            "gate_id": result["gate_id"],
            "log_id": result["log_id"],
            "scan_method": request.scan_method,
            "security_level": result["security_level"],
            "decision_reason": result["decision_reason"],
            "message": "Access granted" if result["access_granted"] else f"Access denied: {result['decision_reason']}",
            "alert_ids": result.get("alert_ids", [])
        }
        
        # Add error details if verification failed
        if not result["access_granted"] and user_verification:
            response["error_code"] = user_verification.get("error_code")
            response["error_details"] = user_verification.get("error")
        
        logger.info(f"ID verification result: {result['access_granted']} for {request.id_number}")
        
        return response
        
    except ValueError as e:
        logger.warning(f"ID verification validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"ID verification failed for {request.id_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ID verification failed: {str(e)}"
        )

@router.post("/verify_access")
async def verify_access(
    user_id: Optional[str] = None,
    license_plate: Optional[str] = None,
    gate_id: str = Query(default="MAIN_GATE"),
    scan_method: str = Query(default="manual"),
    db: Session = Depends(get_db)
):
    """
    Comprehensive access verification supporting both ID and vehicle verification
    
    This endpoint implements the core business logic:
    - Access is granted if EITHER user ID OR vehicle is valid
    - Supports dual verification (both ID and vehicle)
    - Comprehensive logging and alert generation
    """
    try:
        if not user_id and not license_plate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either user_id or license_plate"
            )
        
        logger.info(f"Access verification: user={user_id}, vehicle={license_plate}, gate={gate_id}")
        
        verification_service = VerificationService(db)
        
        # Perform comprehensive verification
        result = verification_service.perform_access_verification(
            user_id=user_id,
            license_plate=license_plate,
            gate_id=gate_id,
            scan_method=scan_method
        )
        
        logger.info(f"Access verification result: {result['access_granted']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Access verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Access verification failed: {str(e)}"
        )

@router.get("/user/{user_id}")
async def get_user_info(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user information by ID
    """
    try:
        db_service = DatabaseService(db)
        user_repo = db_service.user_repo
        
        user = user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    department: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List users with filtering options
    """
    try:
        db_service = DatabaseService(db)
        user_repo = db_service.user_repo
        
        if active_only:
            users = user_repo.get_active_users(skip=skip, limit=limit)
        else:
            users = user_repo.get_all(skip=skip, limit=limit)
        
        # Apply filters
        if role:
            from models.user import UserRole
            try:
                role_enum = UserRole(role)
                users = [u for u in users if u.role == role_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}"
                )
        
        if department:
            users = [u for u in users if u.department and u.department.lower() == department.lower()]
        
        return {
            "users": [user.to_dict() for user in users],
            "total": len(users),
            "skip": skip,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )

@router.get("/user/{user_id}")
async def get_user_info(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed user information by ID
    """
    try:
        verification_service = VerificationService(db)
        user_repo = verification_service.user_repo
        
        user = user_repo.get_by_id(user_id.upper())
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user's vehicles
        vehicle_repo = verification_service.vehicle_repo
        user_vehicles = vehicle_repo.get_by_owner(user_id.upper())
        
        # Get recent access logs
        access_repo = verification_service.access_log_repo
        recent_logs = access_repo.get_logs_by_user(user_id.upper(), limit=10)
        
        user_data = user.to_dict()
        user_data["vehicles"] = [vehicle.to_dict() for vehicle in user_vehicles]
        user_data["recent_access"] = [log.to_dict() for log in recent_logs]
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user info for {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user info: {str(e)}"
        )

@router.get("/users")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[str] = Query(None, regex="^(student|staff|faculty)$"),
    department: Optional[str] = None,
    active_only: bool = Query(True),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List users with filtering and search options
    """
    try:
        verification_service = VerificationService(db)
        user_repo = verification_service.user_repo
        
        if search:
            users = user_repo.search_users(search, skip=skip, limit=limit)
        elif active_only:
            users = user_repo.get_active_users(skip=skip, limit=limit)
        else:
            users = user_repo.get_all(skip=skip, limit=limit)
        
        # Apply filters
        if role:
            from models.user import UserRole
            try:
                role_enum = UserRole(role)
                users = [u for u in users if u.role == role_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid role: {role}"
                )
        
        if department:
            users = [u for u in users if u.department and u.department.lower() == department.lower()]
        
        return {
            "users": [user.to_dict() for user in users],
            "total": len(users),
            "skip": skip,
            "limit": limit,
            "filters": {
                "role": role,
                "department": department,
                "active_only": active_only,
                "search": search
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {str(e)}"
        )

@router.get("/verification/statistics")
async def get_verification_statistics(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get verification statistics and analytics
    """
    try:
        verification_service = VerificationService(db)
        stats = verification_service.get_verification_statistics(days=days)
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get verification statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get verification statistics: {str(e)}"
        )

@router.post("/user/{user_id}/activate")
async def activate_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Activate a user account
    """
    try:
        verification_service = VerificationService(db)
        user_repo = verification_service.user_repo
        
        success = user_repo.activate_user(user_id.upper())
        
        if success:
            logger.info(f"User {user_id} activated")
            return {
                "success": True,
                "message": f"User {user_id} activated successfully",
                "user_id": user_id.upper()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {str(e)}"
        )

@router.post("/user/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Deactivate a user account
    """
    try:
        verification_service = VerificationService(db)
        user_repo = verification_service.user_repo
        
        success = user_repo.deactivate_user(user_id.upper())
        
        if success:
            logger.info(f"User {user_id} deactivated")
            return {
                "success": True,
                "message": f"User {user_id} deactivated successfully",
                "user_id": user_id.upper()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )

@router.get("/validate/{user_id}")
async def validate_user_id_format(
    user_id: str
):
    """
    Validate user ID format without database lookup
    Useful for frontend validation
    """
    try:
        verification_service = VerificationService(None)  # No DB needed for format validation
        
        # Basic validation checks
        if not user_id or not user_id.strip():
            return {
                "valid": False,
                "error": "User ID cannot be empty",
                "error_code": "EMPTY_ID"
            }
        
        user_id = user_id.strip().upper()
        
        # Check for suspicious patterns
        if verification_service._is_suspicious_id(user_id):
            return {
                "valid": False,
                "error": "Suspicious ID pattern detected",
                "error_code": "SUSPICIOUS_PATTERN"
            }
        
        # Basic format checks
        if len(user_id) < 3 or len(user_id) > 20:
            return {
                "valid": False,
                "error": "User ID must be between 3 and 20 characters",
                "error_code": "INVALID_LENGTH"
            }
        
        # Must contain alphanumeric characters
        if not any(c.isalnum() for c in user_id):
            return {
                "valid": False,
                "error": "User ID must contain alphanumeric characters",
                "error_code": "INVALID_FORMAT"
            }
        
        return {
            "valid": True,
            "user_id": user_id,
            "message": "User ID format is valid"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate user ID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate user ID: {str(e)}"
        )