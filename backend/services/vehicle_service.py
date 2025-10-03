"""
Vehicle registration and management service
Comprehensive business logic for vehicle operations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Vehicle, User, VehicleType, VehicleStatus, UserStatus
from repositories import VehicleRepository, UserRepository, AccessLogRepository
import re

class VehicleService:
    """
    Service for handling vehicle registration and management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.vehicle_repo = VehicleRepository(db)
        self.user_repo = UserRepository(db)
        self.access_log_repo = AccessLogRepository(db)
    
    def register_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new vehicle with comprehensive validation
        """
        try:
            # Validate and sanitize input data
            validation_result = self._validate_vehicle_data(vehicle_data)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["error"],
                    "error_code": validation_result["error_code"],
                    "vehicle": None
                }
            
            # Use validated data
            validated_data = validation_result["data"]
            
            # Check if license plate already exists
            existing_vehicle = self.vehicle_repo.get_by_license_plate(validated_data["license_plate"])
            if existing_vehicle:
                return {
                    "success": False,
                    "message": f"Vehicle with license plate {validated_data['license_plate']} already exists",
                    "error_code": "DUPLICATE_LICENSE_PLATE",
                    "vehicle": None,
                    "existing_vehicle": {
                        "license_plate": existing_vehicle.license_plate,
                        "owner_name": existing_vehicle.owner.name if existing_vehicle.owner else None,
                        "status": existing_vehicle.status.value
                    }
                }
            
            # Verify owner exists and is active
            if validated_data["owner_id"]:
                owner = self.user_repo.get_by_id(validated_data["owner_id"])
                if not owner:
                    return {
                        "success": False,
                        "message": f"Owner with ID {validated_data['owner_id']} not found",
                        "error_code": "OWNER_NOT_FOUND",
                        "vehicle": None
                    }
                
                if owner.status != UserStatus.ACTIVE:
                    return {
                        "success": False,
                        "message": f"Owner account is {owner.status.value}. Cannot register vehicle for inactive user",
                        "error_code": "INACTIVE_OWNER",
                        "vehicle": None,
                        "owner_details": {
                            "owner_id": owner.id,
                            "owner_name": owner.name,
                            "status": owner.status.value
                        }
                    }
                
                # Check vehicle limit per user
                owner_vehicles = self.vehicle_repo.get_by_owner(validated_data["owner_id"])
                active_vehicles = [v for v in owner_vehicles if v.status == VehicleStatus.ACTIVE]
                
                if len(active_vehicles) >= self._get_vehicle_limit(owner.role):
                    return {
                        "success": False,
                        "message": f"Vehicle limit exceeded. {owner.role.value.title()} can register maximum {self._get_vehicle_limit(owner.role)} vehicles",
                        "error_code": "VEHICLE_LIMIT_EXCEEDED",
                        "vehicle": None,
                        "current_vehicles": len(active_vehicles),
                        "limit": self._get_vehicle_limit(owner.role)
                    }
            
            # Create vehicle
            vehicle = Vehicle.create_from_dict(validated_data)
            created_vehicle = self.vehicle_repo.create_from_model(vehicle)
            
            # Log the registration
            self.access_log_repo.log_access_attempt(
                gate_id="REGISTRATION",
                user_id=validated_data["owner_id"],
                license_plate=validated_data["license_plate"],
                access_granted=True,
                notes=f"Vehicle registration: {validated_data['license_plate']} ({validated_data['vehicle_type']})"
            )
            
            return {
                "success": True,
                "message": "Vehicle registered successfully",
                "error_code": None,
                "vehicle": created_vehicle.to_dict(),
                "registration_timestamp": created_vehicle.registered_at.isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Vehicle registration failed: {str(e)}",
                "error_code": "REGISTRATION_ERROR",
                "vehicle": None
            }
    
    def update_vehicle(self, license_plate: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update vehicle information
        """
        try:
            vehicle = self.vehicle_repo.get_by_license_plate(license_plate.upper())
            if not vehicle:
                return {
                    "success": False,
                    "message": "Vehicle not found",
                    "error_code": "VEHICLE_NOT_FOUND"
                }
            
            # Validate update data
            allowed_fields = ["color", "model", "vehicle_type", "status"]
            validated_updates = {}
            
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    if field == "vehicle_type":
                        try:
                            validated_updates[field] = VehicleType(value.lower())
                        except ValueError:
                            return {
                                "success": False,
                                "message": f"Invalid vehicle type: {value}",
                                "error_code": "INVALID_VEHICLE_TYPE"
                            }
                    elif field == "status":
                        try:
                            validated_updates[field] = VehicleStatus(value.lower())
                        except ValueError:
                            return {
                                "success": False,
                                "message": f"Invalid status: {value}",
                                "error_code": "INVALID_STATUS"
                            }
                    else:
                        validated_updates[field] = str(value).strip()
            
            # Update vehicle
            updated_vehicle = self.vehicle_repo.update(license_plate, validated_updates)
            
            return {
                "success": True,
                "message": "Vehicle updated successfully",
                "vehicle": updated_vehicle.to_dict() if updated_vehicle else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Vehicle update failed: {str(e)}",
                "error_code": "UPDATE_ERROR"
            }
    
    def transfer_ownership(self, license_plate: str, new_owner_id: str) -> Dict[str, Any]:
        """
        Transfer vehicle ownership to another user
        """
        try:
            # Validate new owner
            new_owner = self.user_repo.get_by_id(new_owner_id.upper())
            if not new_owner:
                return {
                    "success": False,
                    "message": f"New owner with ID {new_owner_id} not found",
                    "error_code": "NEW_OWNER_NOT_FOUND"
                }
            
            if new_owner.status != UserStatus.ACTIVE:
                return {
                    "success": False,
                    "message": f"New owner account is {new_owner.status.value}",
                    "error_code": "INACTIVE_NEW_OWNER"
                }
            
            # Check vehicle limit for new owner
            owner_vehicles = self.vehicle_repo.get_by_owner(new_owner_id.upper())
            active_vehicles = [v for v in owner_vehicles if v.status == VehicleStatus.ACTIVE]
            
            if len(active_vehicles) >= self._get_vehicle_limit(new_owner.role):
                return {
                    "success": False,
                    "message": f"New owner has reached vehicle limit ({self._get_vehicle_limit(new_owner.role)})",
                    "error_code": "NEW_OWNER_VEHICLE_LIMIT"
                }
            
            # Transfer ownership
            success = self.vehicle_repo.transfer_ownership(license_plate.upper(), new_owner_id.upper())
            
            if success:
                # Log the transfer
                self.access_log_repo.log_access_attempt(
                    gate_id="TRANSFER",
                    user_id=new_owner_id.upper(),
                    license_plate=license_plate.upper(),
                    access_granted=True,
                    notes=f"Vehicle ownership transferred to {new_owner.name}"
                )
                
                return {
                    "success": True,
                    "message": f"Vehicle ownership transferred to {new_owner.name}",
                    "new_owner": {
                        "owner_id": new_owner.id,
                        "owner_name": new_owner.name,
                        "owner_role": new_owner.role.value
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Vehicle not found",
                    "error_code": "VEHICLE_NOT_FOUND"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Ownership transfer failed: {str(e)}",
                "error_code": "TRANSFER_ERROR"
            }
    
    def get_vehicle_history(self, license_plate: str) -> Dict[str, Any]:
        """
        Get comprehensive vehicle history including access logs
        """
        try:
            vehicle = self.vehicle_repo.get_by_license_plate(license_plate.upper())
            if not vehicle:
                return {
                    "success": False,
                    "message": "Vehicle not found",
                    "error_code": "VEHICLE_NOT_FOUND"
                }
            
            # Get access logs
            access_logs = self.access_log_repo.get_logs_by_vehicle(license_plate.upper(), limit=50)
            
            # Get statistics
            total_access = len(access_logs)
            successful_access = sum(1 for log in access_logs if log.access_granted)
            failed_access = total_access - successful_access
            
            # Get recent activity
            recent_logs = access_logs[:10]  # Last 10 attempts
            
            return {
                "success": True,
                "vehicle": vehicle.to_dict(),
                "statistics": {
                    "total_access_attempts": total_access,
                    "successful_access": successful_access,
                    "failed_access": failed_access,
                    "success_rate": (successful_access / total_access * 100) if total_access > 0 else 0
                },
                "recent_activity": [log.to_dict() for log in recent_logs],
                "access_history": [log.to_dict() for log in access_logs]
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get vehicle history: {str(e)}",
                "error_code": "HISTORY_ERROR"
            }
    
    def search_vehicles(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search vehicles with multiple criteria
        """
        try:
            # Extract search parameters
            license_plate = search_params.get("license_plate")
            owner_id = search_params.get("owner_id")
            vehicle_type = search_params.get("vehicle_type")
            color = search_params.get("color")
            status = search_params.get("status", "active")
            limit = min(search_params.get("limit", 50), 200)  # Max 200 results
            
            # Start with all vehicles or filter by status
            if status == "active":
                vehicles = self.vehicle_repo.get_active_vehicles(limit=1000)  # Get more for filtering
            else:
                vehicles = self.vehicle_repo.get_all(limit=1000)
            
            # Apply filters
            if license_plate:
                vehicles = [v for v in vehicles if license_plate.upper() in v.license_plate.upper()]
            
            if owner_id:
                vehicles = [v for v in vehicles if v.owner_id and owner_id.upper() in v.owner_id.upper()]
            
            if vehicle_type:
                try:
                    type_enum = VehicleType(vehicle_type.lower())
                    vehicles = [v for v in vehicles if v.vehicle_type == type_enum]
                except ValueError:
                    return {
                        "success": False,
                        "message": f"Invalid vehicle type: {vehicle_type}",
                        "error_code": "INVALID_VEHICLE_TYPE"
                    }
            
            if color:
                vehicles = [v for v in vehicles if v.color and color.lower() in v.color.lower()]
            
            # Limit results
            vehicles = vehicles[:limit]
            
            return {
                "success": True,
                "vehicles": [vehicle.to_dict() for vehicle in vehicles],
                "total_found": len(vehicles),
                "search_params": search_params
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Vehicle search failed: {str(e)}",
                "error_code": "SEARCH_ERROR"
            }
    
    def _validate_vehicle_data(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and sanitize vehicle registration data
        """
        # Required fields
        required_fields = ["license_plate", "owner_id", "vehicle_type"]
        
        for field in required_fields:
            if field not in vehicle_data or not vehicle_data[field]:
                return {
                    "valid": False,
                    "error": f"Missing required field: {field}",
                    "error_code": "MISSING_REQUIRED_FIELD"
                }
        
        # Sanitize and validate license plate
        license_plate = str(vehicle_data["license_plate"]).strip().upper()
        if not self._is_valid_license_plate(license_plate):
            return {
                "valid": False,
                "error": "Invalid license plate format",
                "error_code": "INVALID_LICENSE_PLATE"
            }
        
        # Validate owner ID
        owner_id = str(vehicle_data["owner_id"]).strip().upper()
        if len(owner_id) < 3 or len(owner_id) > 20:
            return {
                "valid": False,
                "error": "Owner ID must be between 3 and 20 characters",
                "error_code": "INVALID_OWNER_ID"
            }
        
        # Validate vehicle type
        try:
            vehicle_type = VehicleType(str(vehicle_data["vehicle_type"]).lower())
        except ValueError:
            return {
                "valid": False,
                "error": f"Invalid vehicle type. Must be one of: {', '.join([t.value for t in VehicleType])}",
                "error_code": "INVALID_VEHICLE_TYPE"
            }
        
        # Optional fields with validation
        color = str(vehicle_data.get("color", "")).strip() if vehicle_data.get("color") else None
        if color and len(color) > 30:
            return {
                "valid": False,
                "error": "Color must be 30 characters or less",
                "error_code": "INVALID_COLOR"
            }
        
        model = str(vehicle_data.get("model", "")).strip() if vehicle_data.get("model") else None
        if model and len(model) > 50:
            return {
                "valid": False,
                "error": "Model must be 50 characters or less",
                "error_code": "INVALID_MODEL"
            }
        
        return {
            "valid": True,
            "data": {
                "license_plate": license_plate,
                "owner_id": owner_id,
                "vehicle_type": vehicle_type,
                "color": color,
                "model": model,
                "status": VehicleStatus.ACTIVE
            }
        }
    
    def _is_valid_license_plate(self, license_plate: str) -> bool:
        """
        Validate license plate format
        """
        # Remove spaces and convert to uppercase
        plate = license_plate.replace(" ", "").upper()
        
        # Basic length check (3-10 characters)
        if len(plate) < 3 or len(plate) > 10:
            return False
        
        # Must contain at least one alphanumeric character
        if not any(c.isalnum() for c in plate):
            return False
        
        # Must not contain only special characters
        if not re.match(r'^[A-Z0-9\-]+$', plate):
            return False
        
        # Must not be all the same character
        if len(set(plate)) == 1:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = ["TEST", "FAKE", "DEMO", "INVALID", "NULL"]
        for pattern in suspicious_patterns:
            if pattern in plate:
                return False
        
        return True
    
    def _get_vehicle_limit(self, user_role) -> int:
        """
        Get vehicle registration limit based on user role
        """
        from models.user import UserRole
        
        limits = {
            UserRole.STUDENT: 2,    # Students can register up to 2 vehicles
            UserRole.STAFF: 3,      # Staff can register up to 3 vehicles
            UserRole.FACULTY: 5     # Faculty can register up to 5 vehicles
        }
        
        return limits.get(user_role, 1)  # Default limit is 1
    
    def get_registration_statistics(self) -> Dict[str, Any]:
        """
        Get vehicle registration statistics
        """
        try:
            stats = self.vehicle_repo.get_vehicle_statistics()
            
            # Get registration trends (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_vehicles = self.db.query(Vehicle).filter(
                Vehicle.registered_at >= thirty_days_ago
            ).all()
            
            # Group by day
            daily_registrations = {}
            for vehicle in recent_vehicles:
                date_key = vehicle.registered_at.date().isoformat()
                daily_registrations[date_key] = daily_registrations.get(date_key, 0) + 1
            
            return {
                "overall_statistics": stats,
                "recent_registrations": {
                    "last_30_days": len(recent_vehicles),
                    "daily_breakdown": daily_registrations
                },
                "limits_by_role": {
                    "student": self._get_vehicle_limit(UserRole.STUDENT),
                    "staff": self._get_vehicle_limit(UserRole.STAFF),
                    "faculty": self._get_vehicle_limit(UserRole.FACULTY)
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get registration statistics: {str(e)}"
            }