"""
Vehicle management router
Enhanced with comprehensive vehicle registration and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from database.connection import get_db
from services.vehicle_service import VehicleService
from services.verification_service import VerificationService
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

class VehicleRegistrationRequest(BaseModel):
    license_plate: str = Field(..., min_length=3, max_length=10, description="Vehicle license plate")
    owner_id: str = Field(..., min_length=3, max_length=20, description="Owner user ID")
    vehicle_type: str = Field(..., regex="^(car|motorcycle|bicycle)$", description="Type of vehicle")
    color: Optional[str] = Field(None, max_length=30, description="Vehicle color")
    model: Optional[str] = Field(None, max_length=50, description="Vehicle model")

class VehicleUpdateRequest(BaseModel):
    color: Optional[str] = Field(None, max_length=30)
    model: Optional[str] = Field(None, max_length=50)
    vehicle_type: Optional[str] = Field(None, regex="^(car|motorcycle|bicycle)$")
    status: Optional[str] = Field(None, regex="^(active|inactive)$")

class OwnershipTransferRequest(BaseModel):
    new_owner_id: str = Field(..., min_length=3, max_length=20, description="New owner user ID")

@router.post("/register")
async def register_vehicle(
    request: VehicleRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new vehicle in the system with comprehensive validation
    
    This endpoint handles vehicle registration with:
    - License plate format validation and duplicate checking
    - Owner verification and status checking
    - Vehicle type validation
    - Vehicle limit enforcement per user role
    - Comprehensive error handling and logging
    
    Returns detailed registration results including vehicle information
    and any validation errors.
    """
    try:
        logger.info(f"Vehicle registration request: {request.license_plate} for owner {request.owner_id}")
        
        vehicle_service = VehicleService(db)
        
        # Prepare vehicle data
        vehicle_data = {
            "license_plate": request.license_plate,
            "owner_id": request.owner_id,
            "vehicle_type": request.vehicle_type,
            "color": request.color,
            "model": request.model
        }
        
        # Register vehicle
        result = vehicle_service.register_vehicle(vehicle_data)
        
        if result["success"]:
            logger.info(f"Vehicle registered successfully: {request.license_plate}")
            return {
                "success": True,
                "message": result["message"],
                "vehicle": result["vehicle"],
                "registration_timestamp": result.get("registration_timestamp")
            }
        else:
            logger.warning(f"Vehicle registration failed: {result['message']}")
            
            # Return appropriate HTTP status based on error type
            if result["error_code"] in ["DUPLICATE_LICENSE_PLATE", "VEHICLE_LIMIT_EXCEEDED"]:
                status_code = status.HTTP_409_CONFLICT
            elif result["error_code"] in ["OWNER_NOT_FOUND", "INACTIVE_OWNER"]:
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            raise HTTPException(
                status_code=status_code,
                detail={
                    "error": result["message"],
                    "error_code": result["error_code"],
                    "details": {k: v for k, v in result.items() if k not in ["success", "message", "error_code", "vehicle"]}
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vehicle registration error for {request.license_plate}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vehicle registration failed: {str(e)}"
        )





@router.get("/{license_plate}")
async def get_vehicle_info(
    license_plate: str,
    db: Session = Depends(get_db)
):
    """
    Get vehicle information by license plate
    """
    try:
        db_service = DatabaseService(db)
        vehicle_repo = db_service.vehicle_repo
        
        vehicle = vehicle_repo.get_by_license_plate(license_plate.upper())
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
        
        return vehicle.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vehicle info: {str(e)}"
        )

@router.get("/")
async def list_vehicles(
    skip: int = 0,
    limit: int = 100,
    owner_id: Optional[str] = None,
    vehicle_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    List vehicles with filtering options
    """
    try:
        db_service = DatabaseService(db)
        vehicle_repo = db_service.vehicle_repo
        
        if active_only:
            vehicles = vehicle_repo.get_active_vehicles(skip=skip, limit=limit)
        else:
            vehicles = vehicle_repo.get_all(skip=skip, limit=limit)
        
        # Apply filters
        if owner_id:
            vehicles = [v for v in vehicles if v.owner_id == owner_id]
        
        if vehicle_type:
            from models.vehicle import VehicleType
            try:
                type_enum = VehicleType(vehicle_type.lower())
                vehicles = [v for v in vehicles if v.vehicle_type == type_enum]
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid vehicle type: {vehicle_type}"
                )
        
        return {
            "vehicles": [vehicle.to_dict() for vehicle in vehicles],
            "total": len(vehicles),
            "skip": skip,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vehicles: {str(e)}"
        )
@rou
ter.put("/{license_plate}")
async def update_vehicle(
    license_plate: str,
    request: VehicleUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update vehicle information
    """
    try:
        vehicle_service = VehicleService(db)
        
        # Convert request to dict, excluding None values
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        result = vehicle_service.update_vehicle(license_plate, update_data)
        
        if result["success"]:
            return result
        else:
            if result["error_code"] == "VEHICLE_NOT_FOUND":
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["message"]
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vehicle update error for {license_plate}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vehicle update failed: {str(e)}"
        )

@router.post("/{license_plate}/transfer")
async def transfer_ownership(
    license_plate: str,
    request: OwnershipTransferRequest,
    db: Session = Depends(get_db)
):
    """
    Transfer vehicle ownership to another user
    """
    try:
        vehicle_service = VehicleService(db)
        
        result = vehicle_service.transfer_ownership(license_plate, request.new_owner_id)
        
        if result["success"]:
            logger.info(f"Vehicle ownership transferred: {license_plate} to {request.new_owner_id}")
            return result
        else:
            if result["error_code"] in ["VEHICLE_NOT_FOUND", "NEW_OWNER_NOT_FOUND"]:
                status_code = status.HTTP_404_NOT_FOUND
            elif result["error_code"] in ["INACTIVE_NEW_OWNER", "NEW_OWNER_VEHICLE_LIMIT"]:
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            
            raise HTTPException(
                status_code=status_code,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ownership transfer error for {license_plate}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ownership transfer failed: {str(e)}"
        )

@router.post("/verify/{license_plate}")
async def verify_vehicle(
    license_plate: str,
    gate_id: str = Query(default="MAIN_GATE", description="Gate identifier"),
    db: Session = Depends(get_db)
):
    """
    Verify vehicle by license plate with comprehensive validation
    """
    try:
        logger.info(f"Vehicle verification request: {license_plate} at {gate_id}")
        
        verification_service = VerificationService(db)
        
        # Perform access verification
        result = verification_service.perform_access_verification(
            license_plate=license_plate,
            gate_id=gate_id
        )
        
        # Extract vehicle verification details
        vehicle_verification = result.get("vehicle_verification", {})
        
        # Format response for API consumers
        response = {
            "access_granted": result["access_granted"],
            "license_plate": license_plate.upper(),
            "owner_name": vehicle_verification.get("owner_name"),
            "owner_id": vehicle_verification.get("owner_id"),
            "vehicle_type": vehicle_verification.get("vehicle_type"),
            "vehicle_color": vehicle_verification.get("color"),
            "vehicle_model": vehicle_verification.get("model"),
            "verification_method": result["verification_method"],
            "timestamp": result["timestamp"],
            "gate_id": result["gate_id"],
            "log_id": result["log_id"],
            "security_level": result["security_level"],
            "decision_reason": result["decision_reason"],
            "message": "Vehicle authorized" if result["access_granted"] else f"Unauthorized vehicle: {result['decision_reason']}",
            "alert_ids": result.get("alert_ids", [])
        }
        
        # Add error details if verification failed
        if not result["access_granted"] and vehicle_verification:
            response["error_code"] = vehicle_verification.get("error_code")
            response["error_details"] = vehicle_verification.get("error")
        
        logger.info(f"Vehicle verification result: {result['access_granted']} for {license_plate}")
        
        return response
        
    except Exception as e:
        logger.error(f"Vehicle verification failed for {license_plate}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vehicle verification failed: {str(e)}"
        )

@router.post("/upload_video")
async def upload_video(
    video_file: UploadFile = File(...),
    gate_id: str = Query(default="MAIN_GATE", description="Gate identifier"),
    db: Session = Depends(get_db)
):
    """
    Upload vehicle video for license plate recognition using OpenCV and EasyOCR
    
    This endpoint accepts video files and processes them for license plate detection
    using computer vision and OCR technology.
    
    Supports common video formats (MP4, AVI, MOV) up to 10MB.
    Returns detected license plate and verification results.
    """
    try:
        # Import OCR service
        from services.ocr_service import OCRService
        from config.ocr_config import OCRConfig
        import time
        
        # Validate file type
        if not video_file.content_type or not video_file.content_type.startswith('video/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a video (MP4, AVI, MOV, etc.)"
            )
        
        # Check if file format is supported
        if not OCRConfig.is_supported_format(video_file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported video format. Supported formats: {', '.join(OCRConfig.SUPPORTED_VIDEO_FORMATS)}"
            )
        
        # Read file content
        content = await video_file.read()
        
        # Validate file size using configuration
        max_size = OCRConfig.get_max_video_size_bytes()
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size must be less than {OCRConfig.MAX_VIDEO_SIZE_MB}MB"
            )
        
        logger.info(f"Video upload: {video_file.filename} ({len(content)} bytes) at {gate_id}")
        
        # Initialize OCR service
        try:
            ocr_service = OCRService()
        except Exception as e:
            logger.error(f"Failed to initialize OCR service: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OCR service initialization failed"
            )
        
        # Save uploaded file temporarily
        temp_file_path = None
        try:
            processing_start = time.time()
            
            # Save file to temporary location
            temp_file_path = ocr_service.save_uploaded_file(content, video_file.filename)
            
            # Process video for license plate detection
            detected_plate = ocr_service.process_video(temp_file_path)
            
            processing_time = time.time() - processing_start
            
            # Prepare OCR results
            ocr_results = {
                "method": "opencv_easyocr",
                "detection_status": "success" if detected_plate else "no_plate_detected",
                "processing_time": round(processing_time, 2)
            }
            
            if detected_plate:
                ocr_results["license_plate"] = detected_plate
                ocr_results["confidence"] = 0.85  # EasyOCR provides confidence, using default for now
                
                # Verify detected plate against database
                verification_service = VerificationService(db)
                result = verification_service.perform_access_verification(
                    license_plate=detected_plate,
                    gate_id=gate_id
                )
                
                verification_results = {
                    "access_granted": result["access_granted"],
                    "verification_method": result["verification_method"],
                    "timestamp": result["timestamp"],
                    "gate_id": result["gate_id"],
                    "log_id": result["log_id"],
                    "security_level": result["security_level"],
                    "decision_reason": result["decision_reason"]
                }
                
                message = f"License plate detected: {detected_plate}. " + \
                         ("Access granted" if result["access_granted"] else f"Access denied: {result['decision_reason']}")
                
            else:
                # No license plate detected
                verification_results = {
                    "access_granted": False,
                    "verification_method": "video_ocr",
                    "timestamp": None,
                    "gate_id": gate_id,
                    "log_id": None,
                    "security_level": "denied",
                    "decision_reason": "No license plate detected in video"
                }
                
                message = "No license plate could be detected in the uploaded video"
            
            response = {
                "success": True,
                "filename": video_file.filename,
                "file_size": len(content),
                "processing_time": round(processing_time, 2),
                "ocr_results": ocr_results,
                "verification": verification_results,
                "message": message
            }
            
            logger.info(f"Video processing complete: {detected_plate or 'No plate detected'}")
            
            return response
            
        finally:
            # Clean up temporary file
            if temp_file_path:
                ocr_service.cleanup_temp_file(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing failed: {str(e)}"
        )

@router.get("/{license_plate}")
async def get_vehicle_info(
    license_plate: str,
    include_history: bool = Query(False, description="Include access history"),
    db: Session = Depends(get_db)
):
    """
    Get detailed vehicle information by license plate
    """
    try:
        vehicle_service = VehicleService(db)
        
        if include_history:
            result = vehicle_service.get_vehicle_history(license_plate)
            if result["success"]:
                return result
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result["message"]
                )
        else:
            vehicle = vehicle_service.vehicle_repo.get_by_license_plate(license_plate.upper())
            if not vehicle:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vehicle not found"
                )
            
            return {
                "success": True,
                "vehicle": vehicle.to_dict()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vehicle info for {license_plate}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vehicle info: {str(e)}"
        )

@router.get("/")
async def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    owner_id: Optional[str] = Query(None, description="Filter by owner ID"),
    vehicle_type: Optional[str] = Query(None, regex="^(car|motorcycle|bicycle)$"),
    color: Optional[str] = Query(None, description="Filter by color"),
    status: str = Query("active", regex="^(active|inactive|all)$"),
    search: Optional[str] = Query(None, description="Search license plates"),
    db: Session = Depends(get_db)
):
    """
    List vehicles with comprehensive filtering options
    """
    try:
        vehicle_service = VehicleService(db)
        
        # Prepare search parameters
        search_params = {
            "limit": limit,
            "status": status,
        }
        
        if owner_id:
            search_params["owner_id"] = owner_id
        if vehicle_type:
            search_params["vehicle_type"] = vehicle_type
        if color:
            search_params["color"] = color
        if search:
            search_params["license_plate"] = search
        
        # Perform search
        result = vehicle_service.search_vehicles(search_params)
        
        if result["success"]:
            return {
                "vehicles": result["vehicles"],
                "total": result["total_found"],
                "skip": skip,
                "limit": limit,
                "filters": {
                    "owner_id": owner_id,
                    "vehicle_type": vehicle_type,
                    "color": color,
                    "status": status,
                    "search": search
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list vehicles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vehicles: {str(e)}"
        )

@router.get("/owner/{owner_id}")
async def get_owner_vehicles(
    owner_id: str,
    active_only: bool = Query(True, description="Show only active vehicles"),
    db: Session = Depends(get_db)
):
    """
    Get all vehicles owned by a specific user
    """
    try:
        vehicle_service = VehicleService(db)
        
        vehicles = vehicle_service.vehicle_repo.get_by_owner(owner_id.upper())
        
        if active_only:
            from models.vehicle import VehicleStatus
            vehicles = [v for v in vehicles if v.status == VehicleStatus.ACTIVE]
        
        return {
            "owner_id": owner_id.upper(),
            "vehicles": [vehicle.to_dict() for vehicle in vehicles],
            "total": len(vehicles),
            "active_only": active_only
        }
        
    except Exception as e:
        logger.error(f"Failed to get vehicles for owner {owner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get owner vehicles: {str(e)}"
        )

@router.get("/statistics/registration")
async def get_registration_statistics(
    db: Session = Depends(get_db)
):
    """
    Get vehicle registration statistics and analytics
    """
    try:
        vehicle_service = VehicleService(db)
        stats = vehicle_service.get_registration_statistics()
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get registration statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get registration statistics: {str(e)}"
        )

@router.post("/{license_plate}/activate")
async def activate_vehicle(
    license_plate: str,
    db: Session = Depends(get_db)
):
    """
    Activate a vehicle registration
    """
    try:
        vehicle_service = VehicleService(db)
        
        success = vehicle_service.vehicle_repo.activate_vehicle(license_plate.upper())
        
        if success:
            logger.info(f"Vehicle {license_plate} activated")
            return {
                "success": True,
                "message": f"Vehicle {license_plate.upper()} activated successfully",
                "license_plate": license_plate.upper()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate vehicle {license_plate}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate vehicle: {str(e)}"
        )

@router.post("/{license_plate}/deactivate")
async def deactivate_vehicle(
    license_plate: str,
    db: Session = Depends(get_db)
):
    """
    Deactivate a vehicle registration
    """
    try:
        vehicle_service = VehicleService(db)
        
        success = vehicle_service.vehicle_repo.deactivate_vehicle(license_plate.upper())
        
        if success:
            logger.info(f"Vehicle {license_plate} deactivated")
            return {
                "success": True,
                "message": f"Vehicle {license_plate.upper()} deactivated successfully",
                "license_plate": license_plate.upper()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate vehicle {license_plate}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate vehicle: {str(e)}"
        )