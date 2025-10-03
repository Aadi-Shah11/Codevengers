"""
Database service layer that coordinates repository operations
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from repositories import UserRepository, VehicleRepository, AccessLogRepository, AlertRepository
from models import User, Vehicle, AccessLog, Alert, VerificationMethod

class DatabaseService:
    """
    Service layer that coordinates database operations across repositories
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.vehicle_repo = VehicleRepository(db)
        self.access_log_repo = AccessLogRepository(db)
        self.alert_repo = AlertRepository(db)
    
    def verify_access(self, user_id: Optional[str] = None, 
                     license_plate: Optional[str] = None,
                     gate_id: str = "MAIN_GATE") -> Dict[str, Any]:
        """
        Comprehensive access verification with logging
        Implements the core business logic: access granted if either ID OR vehicle is valid
        """
        
        if not user_id and not license_plate:
            raise ValueError("Must provide either user_id or license_plate")
        
        # Verify user if provided
        user_verification = None
        if user_id:
            user_verification = self.user_repo.verify_user_id(user_id)
        
        # Verify vehicle if provided
        vehicle_verification = None
        if license_plate:
            vehicle_verification = self.vehicle_repo.verify_vehicle(license_plate)
        
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
        
        # Create notes
        notes = []
        if user_verification:
            notes.append(f"User verification: {'VALID' if user_valid else 'INVALID'}")
        if vehicle_verification:
            notes.append(f"Vehicle verification: {'VALID' if vehicle_valid else 'INVALID'}")
        
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
        if not access_granted:
            if user_id and not user_valid:
                self.alert_repo.create_unauthorized_id_alert(user_id, gate_id)
            if license_plate and not vehicle_valid:
                self.alert_repo.create_unauthorized_vehicle_alert(license_plate, gate_id)
        
        # Prepare response
        response = {
            "access_granted": access_granted,
            "verification_method": verification_method.value,
            "gate_id": gate_id,
            "timestamp": access_log.timestamp.isoformat(),
            "log_id": access_log.id,
            "user_verification": user_verification,
            "vehicle_verification": vehicle_verification,
            "notes": notes_text
        }
        
        return response
    
    def register_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new vehicle with comprehensive validation"""
        try:
            # Register vehicle
            vehicle = self.vehicle_repo.register_vehicle(vehicle_data)
            
            # Log the registration
            self.access_log_repo.log_access_attempt(
                gate_id="REGISTRATION",
                user_id=vehicle.owner_id,
                license_plate=vehicle.license_plate,
                verification_method=VerificationMethod.BOTH,
                access_granted=True,
                notes=f"Vehicle registration: {vehicle.display_name}"
            )
            
            return {
                "success": True,
                "message": "Vehicle registered successfully",
                "vehicle": vehicle.to_dict()
            }
            
        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
                "vehicle": None
            }
    
    def get_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        
        # Access statistics
        access_stats = self.access_log_repo.get_access_statistics(days)
        
        # Alert statistics
        alert_stats = self.alert_repo.get_alert_statistics(days)
        
        # Recent logs
        recent_logs = self.access_log_repo.get_recent_logs(limit=20)
        
        # Active alerts
        active_alerts = self.alert_repo.get_active_alerts(limit=10)
        
        # User and vehicle counts
        user_stats = self.user_repo.get_user_statistics()
        vehicle_stats = self.vehicle_repo.get_vehicle_statistics()
        
        return {
            "access_statistics": access_stats,
            "alert_statistics": alert_stats,
            "user_statistics": user_stats,
            "vehicle_statistics": vehicle_stats,
            "recent_logs": [log.to_dict() for log in recent_logs],
            "active_alerts": [alert.to_dict() for alert in active_alerts],
            "period_days": days
        }
    
    def get_access_logs(self, limit: int = 50, skip: int = 0, 
                       gate_id: Optional[str] = None,
                       user_id: Optional[str] = None,
                       license_plate: Optional[str] = None) -> Dict[str, Any]:
        """Get filtered access logs"""
        
        if gate_id:
            logs = self.access_log_repo.get_logs_by_gate(gate_id, limit, skip)
        elif user_id:
            logs = self.access_log_repo.get_logs_by_user(user_id, limit, skip)
        elif license_plate:
            logs = self.access_log_repo.get_logs_by_vehicle(license_plate, limit, skip)
        else:
            logs = self.access_log_repo.get_recent_logs(limit, skip)
        
        return {
            "logs": [log.to_dict() for log in logs],
            "total_count": len(logs),
            "limit": limit,
            "skip": skip
        }
    
    def get_alerts(self, limit: int = 50, skip: int = 0,
                  active_only: bool = True) -> Dict[str, Any]:
        """Get alerts with filtering"""
        
        if active_only:
            alerts = self.alert_repo.get_active_alerts(limit, skip)
        else:
            alerts = self.alert_repo.get_all(skip, limit)
        
        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "total_count": len(alerts),
            "limit": limit,
            "skip": skip,
            "active_only": active_only
        }
    
    def resolve_alert(self, alert_id: int) -> Dict[str, Any]:
        """Resolve an alert"""
        success = self.alert_repo.resolve_alert(alert_id)
        
        return {
            "success": success,
            "message": "Alert resolved successfully" if success else "Alert not found or already resolved",
            "alert_id": alert_id
        }
    
    def search_data(self, search_term: str, limit: int = 50) -> Dict[str, Any]:
        """Search across users, vehicles, logs, and alerts"""
        
        # Search users
        users = self.user_repo.search_users(search_term, limit=limit)
        
        # Search vehicles
        vehicles = self.vehicle_repo.search_vehicles(search_term, limit=limit)
        
        # Search logs
        logs = self.access_log_repo.search_logs(search_term, limit=limit)
        
        # Search alerts
        alerts = self.alert_repo.search_alerts(search_term, limit=limit)
        
        return {
            "search_term": search_term,
            "results": {
                "users": [user.to_dict() for user in users],
                "vehicles": [vehicle.to_dict() for vehicle in vehicles],
                "logs": [log.to_dict() for log in logs],
                "alerts": [alert.to_dict() for alert in alerts]
            },
            "counts": {
                "users": len(users),
                "vehicles": len(vehicles),
                "logs": len(logs),
                "alerts": len(alerts)
            }
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health information"""
        
        try:
            # Database connection test
            user_count = self.user_repo.count()
            vehicle_count = self.vehicle_repo.count()
            log_count = self.access_log_repo.count()
            alert_count = self.alert_repo.count()
            
            # Recent activity
            recent_logs = self.access_log_repo.get_recent_logs(limit=5)
            active_alerts = self.alert_repo.get_active_alerts(limit=5)
            
            return {
                "status": "healthy",
                "database": {
                    "connection": "ok",
                    "tables": {
                        "users": user_count,
                        "vehicles": vehicle_count,
                        "access_logs": log_count,
                        "alerts": alert_count
                    }
                },
                "recent_activity": {
                    "recent_logs": len(recent_logs),
                    "active_alerts": len(active_alerts)
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database": {
                    "connection": "failed"
                }
            }