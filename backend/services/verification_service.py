"""
ID and access verification service
Core business logic for access control decisions
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import User, Vehicle, AccessLog, Alert, VerificationMethod, UserStatus, VehicleStatus
from repositories import UserRepository, VehicleRepository, AccessLogRepository, AlertRepository

class VerificationService:
    """
    Service for handling ID and vehicle verification logic
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.vehicle_repo = VehicleRepository(db)
        self.access_log_repo = AccessLogRepository(db)
        self.alert_repo = AlertRepository(db)
    
    def verify_user_id(self, user_id: str, scan_method: str = "manual") -> Dict[str, Any]:
        """
        Verify user ID with comprehensive validation
        """
        # Input validation
        if not user_id or not user_id.strip():
            return {
                "is_valid": False,
                "user_id": user_id,
                "error": "User ID cannot be empty",
                "error_code": "EMPTY_ID"
            }
        
        user_id = user_id.strip().upper()
        
        # Check for suspicious patterns
        if self._is_suspicious_id(user_id):
            return {
                "is_valid": False,
                "user_id": user_id,
                "error": "Suspicious ID pattern detected",
                "error_code": "SUSPICIOUS_PATTERN"
            }
        
        # Get user from database
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return {
                "is_valid": False,
                "user_id": user_id,
                "error": "User not found in system",
                "error_code": "USER_NOT_FOUND",
                "scan_method": scan_method
            }
        
        # Check user status
        if user.status != UserStatus.ACTIVE:
            return {
                "is_valid": False,
                "user_id": user_id,
                "user_name": user.name,
                "user_role": user.role.value,
                "user_status": user.status.value,
                "error": f"User account is {user.status.value}",
                "error_code": "INACTIVE_USER",
                "scan_method": scan_method
            }
        
        # Check for recent failed attempts (security measure)
        recent_failures = self._check_recent_failures(user_id)
        if recent_failures["blocked"]:
            return {
                "is_valid": False,
                "user_id": user_id,
                "user_name": user.name,
                "error": f"Too many failed attempts. Try again in {recent_failures['retry_minutes']} minutes",
                "error_code": "TOO_MANY_ATTEMPTS",
                "scan_method": scan_method
            }
        
        # Successful verification
        return {
            "is_valid": True,
            "user_id": user.id,
            "user_name": user.name,
            "user_role": user.role.value,
            "user_department": user.department,
            "user_status": user.status.value,
            "user_email": user.email,
            "scan_method": scan_method,
            "verification_timestamp": datetime.now().isoformat()
        }
    
    def verify_vehicle(self, license_plate: str) -> Dict[str, Any]:
        """
        Verify vehicle with comprehensive validation
        """
        # Input validation
        if not license_plate or not license_plate.strip():
            return {
                "is_valid": False,
                "license_plate": license_plate,
                "error": "License plate cannot be empty",
                "error_code": "EMPTY_PLATE"
            }
        
        license_plate = license_plate.strip().upper()
        
        # Basic format validation
        if not self._is_valid_license_plate_format(license_plate):
            return {
                "is_valid": False,
                "license_plate": license_plate,
                "error": "Invalid license plate format",
                "error_code": "INVALID_FORMAT"
            }
        
        # Get vehicle from database
        vehicle = self.vehicle_repo.get_by_license_plate(license_plate)
        
        if not vehicle:
            return {
                "is_valid": False,
                "license_plate": license_plate,
                "error": "Vehicle not registered in system",
                "error_code": "VEHICLE_NOT_FOUND"
            }
        
        # Check vehicle status
        if vehicle.status != VehicleStatus.ACTIVE:
            return {
                "is_valid": False,
                "license_plate": license_plate,
                "vehicle_type": vehicle.vehicle_type.value,
                "owner_id": vehicle.owner_id,
                "owner_name": vehicle.owner.name if vehicle.owner else None,
                "error": f"Vehicle registration is {vehicle.status.value}",
                "error_code": "INACTIVE_VEHICLE"
            }
        
        # Check owner status if exists
        if vehicle.owner and vehicle.owner.status != UserStatus.ACTIVE:
            return {
                "is_valid": False,
                "license_plate": license_plate,
                "vehicle_type": vehicle.vehicle_type.value,
                "owner_id": vehicle.owner_id,
                "owner_name": vehicle.owner.name,
                "error": f"Vehicle owner account is {vehicle.owner.status.value}",
                "error_code": "INACTIVE_OWNER"
            }
        
        # Successful verification
        return {
            "is_valid": True,
            "license_plate": vehicle.license_plate,
            "vehicle_type": vehicle.vehicle_type.value,
            "color": vehicle.color,
            "model": vehicle.model,
            "owner_id": vehicle.owner_id,
            "owner_name": vehicle.owner.name if vehicle.owner else None,
            "owner_role": vehicle.owner.role.value if vehicle.owner else None,
            "verification_timestamp": datetime.now().isoformat()
        }
    
    def perform_access_verification(self, user_id: Optional[str] = None, 
                                  license_plate: Optional[str] = None,
                                  gate_id: str = "MAIN_GATE",
                                  scan_method: str = "manual") -> Dict[str, Any]:
        """
        Perform comprehensive access verification with logging
        Implements core business rule: access granted if either ID OR vehicle is valid
        """
        
        if not user_id and not license_plate:
            raise ValueError("Must provide either user_id or license_plate")
        
        # Verify user if provided
        user_verification = None
        if user_id:
            user_verification = self.verify_user_id(user_id, scan_method)
        
        # Verify vehicle if provided
        vehicle_verification = None
        if license_plate:
            vehicle_verification = self.verify_vehicle(license_plate)
        
        # Determine verification method
        if user_id and license_plate:
            verification_method = VerificationMethod.BOTH
        elif user_id:
            verification_method = VerificationMethod.ID_ONLY
        else:
            verification_method = VerificationMethod.VEHICLE_ONLY
        
        # Access decision: grant if either verification is valid
        user_valid = user_verification and user_verification.get("is_valid", False)
        vehicle_valid = vehicle_verification and vehicle_verification.get("is_valid", False)
        access_granted = user_valid or vehicle_valid
        
        # Determine primary reason for decision
        if access_granted:
            if user_valid and vehicle_valid:
                decision_reason = "Both ID and vehicle verified successfully"
            elif user_valid:
                decision_reason = "ID verified successfully"
            else:
                decision_reason = "Vehicle verified successfully"
        else:
            reasons = []
            if user_verification and not user_valid:
                reasons.append(f"ID: {user_verification.get('error', 'Invalid')}")
            if vehicle_verification and not vehicle_valid:
                reasons.append(f"Vehicle: {vehicle_verification.get('error', 'Invalid')}")
            decision_reason = "; ".join(reasons) if reasons else "No valid verification method"
        
        # Create comprehensive notes
        notes = [f"Gate: {gate_id}", f"Method: {verification_method.value}"]
        if user_verification:
            notes.append(f"User: {user_verification.get('error_code', 'VALID')}")
        if vehicle_verification:
            notes.append(f"Vehicle: {vehicle_verification.get('error_code', 'VALID')}")
        notes.append(f"Decision: {decision_reason}")
        
        notes_text = "; ".join(notes)
        
        # Log the access attempt
        access_log = self.access_log_repo.log_access_attempt(
            gate_id=gate_id,
            user_id=user_id,
            license_plate=license_plate,
            verification_method=verification_method,
            access_granted=access_granted,
            notes=notes_text
        )
        
        # Create alerts if access denied
        alert_ids = []
        if not access_granted:
            if user_id and not user_valid:
                alert = self.alert_repo.create_unauthorized_id_alert(user_id, gate_id)
                alert_ids.append(alert.id)
            
            if license_plate and not vehicle_valid:
                alert = self.alert_repo.create_unauthorized_vehicle_alert(license_plate, gate_id)
                alert_ids.append(alert.id)
        
        # Prepare comprehensive response
        response = {
            "access_granted": access_granted,
            "verification_method": verification_method.value,
            "gate_id": gate_id,
            "timestamp": access_log.timestamp.isoformat(),
            "log_id": access_log.id,
            "decision_reason": decision_reason,
            "user_verification": user_verification,
            "vehicle_verification": vehicle_verification,
            "alert_ids": alert_ids,
            "notes": notes_text,
            "security_level": self._determine_security_level(user_verification, vehicle_verification, access_granted)
        }
        
        return response
    
    def _is_suspicious_id(self, user_id: str) -> bool:
        """Check for suspicious ID patterns"""
        suspicious_patterns = [
            "TEST", "DEMO", "ADMIN", "ROOT", "HACK", "INVALID", 
            "NULL", "UNDEFINED", "FAKE", "TEMP"
        ]
        
        user_id_upper = user_id.upper()
        
        # Check for suspicious keywords
        for pattern in suspicious_patterns:
            if pattern in user_id_upper:
                return True
        
        # Check for repeated characters (e.g., "AAAA", "1111")
        if len(set(user_id)) <= 2 and len(user_id) > 3:
            return True
        
        # Check for sequential patterns
        if user_id.isdigit() and len(user_id) > 3:
            digits = [int(d) for d in user_id]
            if all(digits[i] + 1 == digits[i + 1] for i in range(len(digits) - 1)):
                return True
        
        return False
    
    def _is_valid_license_plate_format(self, license_plate: str) -> bool:
        """Basic license plate format validation"""
        # Remove spaces and convert to uppercase
        plate = license_plate.replace(" ", "").upper()
        
        # Basic length check (3-10 characters)
        if len(plate) < 3 or len(plate) > 10:
            return False
        
        # Must contain at least one letter or number
        if not any(c.isalnum() for c in plate):
            return False
        
        # Must not be all spaces or special characters
        if not any(c.isalnum() for c in plate):
            return False
        
        return True
    
    def _check_recent_failures(self, user_id: str, minutes: int = 15, max_attempts: int = 5) -> Dict[str, Any]:
        """Check for recent failed attempts to prevent brute force"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        # Get recent failed attempts for this user
        recent_logs = self.db.query(AccessLog).filter(
            AccessLog.user_id == user_id,
            AccessLog.access_granted == False,
            AccessLog.timestamp >= cutoff_time
        ).count()
        
        if recent_logs >= max_attempts:
            return {
                "blocked": True,
                "attempts": recent_logs,
                "max_attempts": max_attempts,
                "retry_minutes": minutes
            }
        
        return {
            "blocked": False,
            "attempts": recent_logs,
            "max_attempts": max_attempts,
            "retry_minutes": 0
        }
    
    def _determine_security_level(self, user_verification: Optional[Dict], 
                                 vehicle_verification: Optional[Dict], 
                                 access_granted: bool) -> str:
        """Determine security level of the access attempt"""
        
        if not access_granted:
            return "HIGH_RISK"
        
        user_valid = user_verification and user_verification.get("is_valid", False)
        vehicle_valid = vehicle_verification and vehicle_verification.get("is_valid", False)
        
        if user_valid and vehicle_valid:
            return "LOW_RISK"
        elif user_valid or vehicle_valid:
            return "MEDIUM_RISK"
        else:
            return "HIGH_RISK"
    
    def get_verification_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get verification statistics for monitoring"""
        
        # Get access statistics
        access_stats = self.access_log_repo.get_access_statistics(days=days)
        
        # Get method breakdown
        start_date = datetime.now() - timedelta(days=days)
        logs = self.db.query(AccessLog).filter(AccessLog.timestamp >= start_date).all()
        
        method_stats = {
            "id_only": 0,
            "vehicle_only": 0,
            "both": 0
        }
        
        for log in logs:
            method_stats[log.verification_method.value] += 1
        
        # Get security level breakdown
        security_stats = {
            "low_risk": 0,
            "medium_risk": 0,
            "high_risk": 0
        }
        
        # This would require storing security level in logs for accurate stats
        # For now, estimate based on verification method and success
        for log in logs:
            if log.access_granted:
                if log.verification_method == VerificationMethod.BOTH:
                    security_stats["low_risk"] += 1
                else:
                    security_stats["medium_risk"] += 1
            else:
                security_stats["high_risk"] += 1
        
        return {
            "period_days": days,
            "access_statistics": access_stats,
            "verification_methods": method_stats,
            "security_levels": security_stats,
            "total_verifications": sum(method_stats.values())
        }