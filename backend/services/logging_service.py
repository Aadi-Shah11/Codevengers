"""
Comprehensive logging service for Smart Campus Access Control
Handles access logs, audit trails, and system monitoring
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, text
from models import AccessLog, Alert, User, Vehicle, VerificationMethod, AlertType
from repositories import AccessLogRepository, AlertRepository, UserRepository, VehicleRepository
import logging
import json

logger = logging.getLogger(__name__)

class LoggingService:
    """
    Service for comprehensive logging and audit trail management
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.access_log_repo = AccessLogRepository(db)
        self.alert_repo = AlertRepository(db)
        self.user_repo = UserRepository(db)
        self.vehicle_repo = VehicleRepository(db)
    
    def log_access_attempt(self, gate_id: str, user_id: Optional[str] = None,
                          license_plate: Optional[str] = None,
                          verification_method: Optional[VerificationMethod] = None,
                          access_granted: bool = False, notes: Optional[str] = None,
                          additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Log an access attempt with comprehensive details
        """
        try:
            # Validate input
            if not user_id and not license_plate:
                raise ValueError("Must provide either user_id or license_plate")
            
            # Determine verification method if not provided
            if not verification_method:
                if user_id and license_plate:
                    verification_method = VerificationMethod.BOTH
                elif user_id:
                    verification_method = VerificationMethod.ID_ONLY
                else:
                    verification_method = VerificationMethod.VEHICLE_ONLY
            
            # Enhance notes with additional context
            enhanced_notes = self._build_enhanced_notes(
                gate_id, user_id, license_plate, verification_method, 
                access_granted, notes, additional_data
            )
            
            # Create access log
            access_log = self.access_log_repo.log_access_attempt(
                gate_id=gate_id,
                user_id=user_id,
                license_plate=license_plate,
                verification_method=verification_method,
                access_granted=access_granted,
                notes=enhanced_notes
            )
            
            # Generate alerts if access denied
            alert_ids = []
            if not access_granted:
                alert_ids = self._generate_security_alerts(
                    gate_id, user_id, license_plate, additional_data
                )
            
            # Log to system logger
            self._log_to_system(access_log, additional_data)
            
            return {
                "success": True,
                "log_id": access_log.id,
                "timestamp": access_log.timestamp.isoformat(),
                "access_granted": access_granted,
                "alert_ids": alert_ids,
                "verification_method": verification_method.value
            }
            
        except Exception as e:
            logger.error(f"Failed to log access attempt: {e}")
            return {
                "success": False,
                "error": str(e),
                "log_id": None
            }
    
    def get_access_logs(self, filters: Dict[str, Any] = None, 
                       pagination: Dict[str, int] = None) -> Dict[str, Any]:
        """
        Get access logs with comprehensive filtering and pagination
        """
        try:
            # Set defaults
            filters = filters or {}
            pagination = pagination or {"limit": 50, "offset": 0}
            
            # Extract filter parameters
            gate_id = filters.get("gate_id")
            user_id = filters.get("user_id")
            license_plate = filters.get("license_plate")
            access_granted = filters.get("access_granted")
            verification_method = filters.get("verification_method")
            start_date = filters.get("start_date")
            end_date = filters.get("end_date")
            search_term = filters.get("search")
            
            # Build query based on filters
            if search_term:
                logs = self.access_log_repo.search_logs(
                    search_term, 
                    limit=pagination["limit"], 
                    skip=pagination["offset"]
                )
            elif start_date and end_date:
                try:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    logs = self.access_log_repo.get_logs_by_date_range(
                        start_dt, end_dt,
                        limit=pagination["limit"],
                        skip=pagination["offset"]
                    )
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Invalid date format: {e}",
                        "logs": []
                    }
            elif gate_id:
                logs = self.access_log_repo.get_logs_by_gate(
                    gate_id,
                    limit=pagination["limit"],
                    skip=pagination["offset"]
                )
            elif user_id:
                logs = self.access_log_repo.get_logs_by_user(
                    user_id,
                    limit=pagination["limit"],
                    skip=pagination["offset"]
                )
            elif license_plate:
                logs = self.access_log_repo.get_logs_by_vehicle(
                    license_plate,
                    limit=pagination["limit"],
                    skip=pagination["offset"]
                )
            else:
                logs = self.access_log_repo.get_recent_logs(
                    limit=pagination["limit"],
                    skip=pagination["offset"]
                )
            
            # Apply additional filters
            if access_granted is not None:
                logs = [log for log in logs if log.access_granted == access_granted]
            
            if verification_method:
                try:
                    method_enum = VerificationMethod(verification_method)
                    logs = [log for log in logs if log.verification_method == method_enum]
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Invalid verification method: {verification_method}",
                        "logs": []
                    }
            
            # Convert to dict format with enhanced data
            logs_data = []
            for log in logs:
                log_dict = log.to_dict()
                
                # Add enhanced information
                log_dict["security_assessment"] = self._assess_log_security(log)
                log_dict["related_alerts"] = self._get_related_alerts(log)
                
                logs_data.append(log_dict)
            
            return {
                "success": True,
                "logs": logs_data,
                "total": len(logs_data),
                "pagination": pagination,
                "filters": filters
            }
            
        except Exception as e:
            logger.error(f"Failed to get access logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": []
            }
    
    def get_access_statistics(self, period_days: int = 7, 
                            gate_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive access statistics
        """
        try:
            # Get basic statistics
            basic_stats = self.access_log_repo.get_access_statistics(
                days=period_days, gate_id=gate_id
            )
            
            # Get hourly patterns
            hourly_patterns = self.access_log_repo.get_hourly_access_pattern(
                days=period_days
            )
            
            # Get daily statistics
            daily_stats = self.access_log_repo.get_daily_statistics(
                days=period_days
            )
            
            # Get verification method breakdown
            method_stats = self._get_verification_method_stats(period_days, gate_id)
            
            # Get security metrics
            security_metrics = self._get_security_metrics(period_days, gate_id)
            
            # Get top users and vehicles
            top_entities = self._get_top_entities(period_days, gate_id)
            
            return {
                "success": True,
                "period_days": period_days,
                "gate_id": gate_id,
                "basic_statistics": basic_stats,
                "hourly_patterns": hourly_patterns,
                "daily_statistics": daily_stats,
                "verification_methods": method_stats,
                "security_metrics": security_metrics,
                "top_entities": top_entities
            }
            
        except Exception as e:
            logger.error(f"Failed to get access statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_audit_trail(self, entity_type: str, entity_id: str,
                       days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive audit trail for a specific entity
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            if entity_type == "user":
                # Get user's access logs
                logs = self.access_log_repo.get_logs_by_user(entity_id, limit=1000)
                
                # Get user's alerts
                alerts = self.alert_repo.get_alerts_by_user(entity_id, limit=100)
                
                # Get user details
                user = self.user_repo.get_by_id(entity_id)
                entity_info = user.to_dict() if user else None
                
            elif entity_type == "vehicle":
                # Get vehicle's access logs
                logs = self.access_log_repo.get_logs_by_vehicle(entity_id, limit=1000)
                
                # Get vehicle's alerts
                alerts = self.alert_repo.get_alerts_by_vehicle(entity_id, limit=100)
                
                # Get vehicle details
                vehicle = self.vehicle_repo.get_by_license_plate(entity_id)
                entity_info = vehicle.to_dict() if vehicle else None
                
            else:
                return {
                    "success": False,
                    "error": f"Invalid entity type: {entity_type}",
                    "audit_trail": []
                }
            
            # Filter by date range
            logs = [log for log in logs if log.timestamp >= start_date]
            alerts = [alert for alert in alerts if alert.created_at >= start_date]
            
            # Combine and sort by timestamp
            audit_events = []
            
            for log in logs:
                audit_events.append({
                    "type": "access_attempt",
                    "timestamp": log.timestamp.isoformat(),
                    "data": log.to_dict(),
                    "summary": f"Access {'granted' if log.access_granted else 'denied'} at {log.gate_id}"
                })
            
            for alert in alerts:
                audit_events.append({
                    "type": "security_alert",
                    "timestamp": alert.created_at.isoformat(),
                    "data": alert.to_dict(),
                    "summary": f"{alert.alert_type.value.replace('_', ' ').title()}: {alert.message[:50]}..."
                })
            
            # Sort by timestamp (newest first)
            audit_events.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # Generate summary statistics
            summary = {
                "total_events": len(audit_events),
                "access_attempts": len(logs),
                "security_alerts": len(alerts),
                "successful_access": sum(1 for log in logs if log.access_granted),
                "failed_access": sum(1 for log in logs if not log.access_granted),
                "active_alerts": sum(1 for alert in alerts if not alert.resolved)
            }
            
            return {
                "success": True,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_info": entity_info,
                "period_days": days,
                "summary": summary,
                "audit_trail": audit_events
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return {
                "success": False,
                "error": str(e),
                "audit_trail": []
            }
    
    def export_logs(self, filters: Dict[str, Any] = None, 
                   format_type: str = "json") -> Dict[str, Any]:
        """
        Export access logs in various formats
        """
        try:
            # Get logs with filters
            logs_result = self.get_access_logs(filters, {"limit": 10000, "offset": 0})
            
            if not logs_result["success"]:
                return logs_result
            
            logs = logs_result["logs"]
            
            if format_type == "json":
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "filters": filters or {},
                    "total_records": len(logs),
                    "logs": logs
                }
                
                return {
                    "success": True,
                    "format": "json",
                    "data": export_data,
                    "filename": f"access_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                }
            
            elif format_type == "csv":
                # Convert to CSV format
                csv_lines = []
                
                # Header
                headers = [
                    "timestamp", "gate_id", "user_id", "user_name", "license_plate",
                    "verification_method", "access_granted", "alert_triggered", "notes"
                ]
                csv_lines.append(",".join(headers))
                
                # Data rows
                for log in logs:
                    row = [
                        log.get("timestamp", ""),
                        log.get("gate_id", ""),
                        log.get("user_id", ""),
                        log.get("user_name", ""),
                        log.get("license_plate", ""),
                        log.get("verification_method", ""),
                        str(log.get("access_granted", "")),
                        str(log.get("alert_triggered", "")),
                        f'"{log.get("notes", "").replace('"', '""')}"'  # Escape quotes
                    ]
                    csv_lines.append(",".join(row))
                
                return {
                    "success": True,
                    "format": "csv",
                    "data": "\n".join(csv_lines),
                    "filename": f"access_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported export format: {format_type}"
                }
                
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> Dict[str, Any]:
        """
        Clean up old access logs and resolved alerts
        """
        try:
            # Clean old access logs
            deleted_logs = self.access_log_repo.cleanup_old_logs(days_to_keep)
            
            # Clean old resolved alerts
            deleted_alerts = self.alert_repo.cleanup_old_alerts(days_to_keep)
            
            logger.info(f"Cleanup completed: {deleted_logs} logs, {deleted_alerts} alerts deleted")
            
            return {
                "success": True,
                "deleted_logs": deleted_logs,
                "deleted_alerts": deleted_alerts,
                "days_kept": days_to_keep,
                "cleanup_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_enhanced_notes(self, gate_id: str, user_id: Optional[str],
                             license_plate: Optional[str], verification_method: VerificationMethod,
                             access_granted: bool, notes: Optional[str],
                             additional_data: Optional[Dict[str, Any]]) -> str:
        """
        Build enhanced notes with additional context
        """
        note_parts = []
        
        # Basic information
        note_parts.append(f"Gate: {gate_id}")
        note_parts.append(f"Method: {verification_method.value}")
        note_parts.append(f"Result: {'GRANTED' if access_granted else 'DENIED'}")
        
        # User information
        if user_id:
            user = self.user_repo.get_by_id(user_id)
            if user:
                note_parts.append(f"User: {user.name} ({user.role.value})")
            else:
                note_parts.append(f"User: {user_id} (NOT FOUND)")
        
        # Vehicle information
        if license_plate:
            vehicle = self.vehicle_repo.get_by_license_plate(license_plate)
            if vehicle:
                note_parts.append(f"Vehicle: {vehicle.display_name}")
                if vehicle.owner:
                    note_parts.append(f"Owner: {vehicle.owner.name}")
            else:
                note_parts.append(f"Vehicle: {license_plate} (NOT REGISTERED)")
        
        # Additional data
        if additional_data:
            for key, value in additional_data.items():
                if key not in ["user_id", "license_plate", "gate_id"]:
                    note_parts.append(f"{key}: {value}")
        
        # Original notes
        if notes:
            note_parts.append(f"Notes: {notes}")
        
        return "; ".join(note_parts)
    
    def _generate_security_alerts(self, gate_id: str, user_id: Optional[str],
                                 license_plate: Optional[str],
                                 additional_data: Optional[Dict[str, Any]]) -> List[int]:
        """
        Generate appropriate security alerts for failed access attempts
        """
        alert_ids = []
        
        try:
            if user_id:
                alert = self.alert_repo.create_unauthorized_id_alert(user_id, gate_id)
                alert_ids.append(alert.id)
            
            if license_plate:
                alert = self.alert_repo.create_unauthorized_vehicle_alert(license_plate, gate_id)
                alert_ids.append(alert.id)
            
            # Generate system error alert if indicated
            if additional_data and additional_data.get("system_error"):
                alert = self.alert_repo.create_system_error_alert(
                    additional_data["system_error"], gate_id
                )
                alert_ids.append(alert.id)
                
        except Exception as e:
            logger.error(f"Failed to generate security alerts: {e}")
        
        return alert_ids
    
    def _log_to_system(self, access_log: AccessLog, additional_data: Optional[Dict[str, Any]]):
        """
        Log access attempt to system logger
        """
        log_level = logging.WARNING if not access_log.access_granted else logging.INFO
        
        log_message = (
            f"Access {'GRANTED' if access_log.access_granted else 'DENIED'} - "
            f"Gate: {access_log.gate_id}, "
            f"Method: {access_log.verification_method.value}, "
            f"User: {access_log.user_id or 'N/A'}, "
            f"Vehicle: {access_log.license_plate or 'N/A'}"
        )
        
        logger.log(log_level, log_message, extra={
            "log_id": access_log.id,
            "gate_id": access_log.gate_id,
            "access_granted": access_log.access_granted,
            "verification_method": access_log.verification_method.value,
            "additional_data": additional_data
        })
    
    def _assess_log_security(self, log: AccessLog) -> Dict[str, Any]:
        """
        Assess security level of an access log
        """
        risk_level = "LOW"
        risk_factors = []
        
        if not log.access_granted:
            risk_level = "HIGH"
            risk_factors.append("Access denied")
        
        if log.alert_triggered:
            risk_level = "HIGH"
            risk_factors.append("Security alert triggered")
        
        # Check for suspicious patterns in notes
        if log.notes:
            suspicious_keywords = ["suspicious", "invalid", "fake", "test", "hack"]
            for keyword in suspicious_keywords:
                if keyword.lower() in log.notes.lower():
                    risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
                    risk_factors.append(f"Suspicious pattern: {keyword}")
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "assessment_timestamp": datetime.now().isoformat()
        }
    
    def _get_related_alerts(self, log: AccessLog) -> List[Dict[str, Any]]:
        """
        Get alerts related to this access log
        """
        related_alerts = []
        
        try:
            # Find alerts created around the same time
            time_window = timedelta(minutes=5)
            start_time = log.timestamp - time_window
            end_time = log.timestamp + time_window
            
            alerts = self.db.query(Alert).filter(
                and_(
                    Alert.created_at >= start_time,
                    Alert.created_at <= end_time,
                    or_(
                        Alert.user_id == log.user_id,
                        Alert.license_plate == log.license_plate
                    )
                )
            ).all()
            
            for alert in alerts:
                related_alerts.append({
                    "alert_id": alert.id,
                    "alert_type": alert.alert_type.value,
                    "message": alert.message,
                    "resolved": alert.resolved
                })
                
        except Exception as e:
            logger.error(f"Failed to get related alerts: {e}")
        
        return related_alerts
    
    def _get_verification_method_stats(self, days: int, gate_id: Optional[str]) -> Dict[str, int]:
        """
        Get verification method statistics
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AccessLog).filter(AccessLog.timestamp >= start_date)
        if gate_id:
            query = query.filter(AccessLog.gate_id == gate_id)
        
        logs = query.all()
        
        method_stats = {
            "id_only": 0,
            "vehicle_only": 0,
            "both": 0
        }
        
        for log in logs:
            method_stats[log.verification_method.value] += 1
        
        return method_stats
    
    def _get_security_metrics(self, days: int, gate_id: Optional[str]) -> Dict[str, Any]:
        """
        Get security-related metrics
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AccessLog).filter(AccessLog.timestamp >= start_date)
        if gate_id:
            query = query.filter(AccessLog.gate_id == gate_id)
        
        logs = query.all()
        
        total_attempts = len(logs)
        failed_attempts = sum(1 for log in logs if not log.access_granted)
        alerts_triggered = sum(1 for log in logs if log.alert_triggered)
        
        # Calculate security score (0-100, higher is better)
        if total_attempts > 0:
            success_rate = (total_attempts - failed_attempts) / total_attempts
            alert_rate = alerts_triggered / total_attempts
            security_score = max(0, min(100, (success_rate * 100) - (alert_rate * 50)))
        else:
            security_score = 100
        
        return {
            "total_attempts": total_attempts,
            "failed_attempts": failed_attempts,
            "alerts_triggered": alerts_triggered,
            "security_score": round(security_score, 2),
            "threat_level": "LOW" if security_score > 80 else "MEDIUM" if security_score > 60 else "HIGH"
        }
    
    def _get_top_entities(self, days: int, gate_id: Optional[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get top users and vehicles by access frequency
        """
        start_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(AccessLog).filter(AccessLog.timestamp >= start_date)
        if gate_id:
            query = query.filter(AccessLog.gate_id == gate_id)
        
        logs = query.all()
        
        # Count by user
        user_counts = {}
        for log in logs:
            if log.user_id:
                user_counts[log.user_id] = user_counts.get(log.user_id, 0) + 1
        
        # Count by vehicle
        vehicle_counts = {}
        for log in logs:
            if log.license_plate:
                vehicle_counts[log.license_plate] = vehicle_counts.get(log.license_plate, 0) + 1
        
        # Get top 5 users
        top_users = []
        for user_id, count in sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            user = self.user_repo.get_by_id(user_id)
            top_users.append({
                "user_id": user_id,
                "user_name": user.name if user else "Unknown",
                "access_count": count
            })
        
        # Get top 5 vehicles
        top_vehicles = []
        for plate, count in sorted(vehicle_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            vehicle = self.vehicle_repo.get_by_license_plate(plate)
            top_vehicles.append({
                "license_plate": plate,
                "vehicle_info": vehicle.display_name if vehicle else "Unknown",
                "access_count": count
            })
        
        return {
            "top_users": top_users,
            "top_vehicles": top_vehicles
        }