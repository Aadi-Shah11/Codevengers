"""
Access Log repository for database operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func, text
from models.access_log import AccessLog, VerificationMethod
from models.user import User
from models.vehicle import Vehicle
from .base_repository import BaseRepository

class AccessLogRepository(BaseRepository[AccessLog]):
    """
    Repository for AccessLog model operations
    """
    
    def __init__(self, db: Session):
        super().__init__(AccessLog, db)
    
    def get_recent_logs(self, limit: int = 50, skip: int = 0) -> List[AccessLog]:
        """Get recent access logs with user and vehicle details"""
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_logs_by_gate(self, gate_id: str, limit: int = 50, skip: int = 0) -> List[AccessLog]:
        """Get access logs for specific gate"""
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .filter(AccessLog.gate_id == gate_id)\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_logs_by_user(self, user_id: str, limit: int = 50, skip: int = 0) -> List[AccessLog]:
        """Get access logs for specific user"""
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .filter(AccessLog.user_id == user_id)\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_logs_by_vehicle(self, license_plate: str, limit: int = 50, skip: int = 0) -> List[AccessLog]:
        """Get access logs for specific vehicle"""
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .filter(AccessLog.license_plate == license_plate)\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_logs_by_date_range(self, start_date: datetime, end_date: datetime, 
                              limit: int = 100, skip: int = 0) -> List[AccessLog]:
        """Get access logs within date range"""
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .filter(and_(AccessLog.timestamp >= start_date, AccessLog.timestamp <= end_date))\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_denied_access_logs(self, limit: int = 50, skip: int = 0) -> List[AccessLog]:
        """Get logs where access was denied"""
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .filter(AccessLog.access_granted == False)\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_alert_logs(self, limit: int = 50, skip: int = 0) -> List[AccessLog]:
        """Get logs that triggered alerts"""
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .filter(AccessLog.alert_triggered == True)\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def log_access_attempt(self, gate_id: str, user_id: Optional[str] = None, 
                          license_plate: Optional[str] = None, 
                          verification_method: Optional[VerificationMethod] = None,
                          access_granted: bool = False, notes: Optional[str] = None) -> AccessLog:
        """Create a new access log entry"""
        
        # Determine verification method if not provided
        if not verification_method:
            if user_id and license_plate:
                verification_method = VerificationMethod.BOTH
            elif user_id:
                verification_method = VerificationMethod.ID_ONLY
            elif license_plate:
                verification_method = VerificationMethod.VEHICLE_ONLY
            else:
                raise ValueError("Must provide either user_id or license_plate")
        
        # Create access log
        access_log = AccessLog.log_access_attempt(
            gate_id=gate_id,
            user_id=user_id,
            license_plate=license_plate,
            verification_method=verification_method,
            access_granted=access_granted,
            notes=notes
        )
        
        return self.create_from_model(access_log)
    
    def get_access_statistics(self, days: int = 7, gate_id: Optional[str] = None) -> Dict[str, Any]:
        """Get access statistics for specified period"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Base query
        query = self.db.query(AccessLog).filter(AccessLog.timestamp >= start_date)
        if gate_id:
            query = query.filter(AccessLog.gate_id == gate_id)
        
        # Get counts
        total_attempts = query.count()
        granted_count = query.filter(AccessLog.access_granted == True).count()
        denied_count = query.filter(AccessLog.access_granted == False).count()
        alert_count = query.filter(AccessLog.alert_triggered == True).count()
        
        # Get unique counts
        unique_users = query.filter(AccessLog.user_id.isnot(None)).distinct(AccessLog.user_id).count()
        unique_vehicles = query.filter(AccessLog.license_plate.isnot(None)).distinct(AccessLog.license_plate).count()
        
        # Calculate success rate
        success_rate = (granted_count / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            "period_days": days,
            "gate_id": gate_id,
            "total_attempts": total_attempts,
            "granted_count": granted_count,
            "denied_count": denied_count,
            "alert_count": alert_count,
            "unique_users": unique_users,
            "unique_vehicles": unique_vehicles,
            "success_rate": round(success_rate, 2)
        }
    
    def get_hourly_access_pattern(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get hourly access patterns"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Raw SQL for better performance with hour extraction
        query = text("""
            SELECT 
                HOUR(timestamp) as access_hour,
                COUNT(*) as total_attempts,
                SUM(CASE WHEN access_granted = 1 THEN 1 ELSE 0 END) as granted_count,
                AVG(CASE WHEN access_granted = 1 THEN 1.0 ELSE 0.0 END) * 100 as success_rate
            FROM access_logs
            WHERE timestamp >= :start_date
            GROUP BY HOUR(timestamp)
            ORDER BY access_hour
        """)
        
        result = self.db.execute(query, {"start_date": start_date}).fetchall()
        
        return [
            {
                "hour": row.access_hour,
                "total_attempts": row.total_attempts,
                "granted_count": row.granted_count,
                "success_rate": round(row.success_rate, 2) if row.success_rate else 0
            }
            for row in result
        ]
    
    def get_daily_statistics(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily access statistics"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Raw SQL for better performance
        query = text("""
            SELECT 
                DATE(timestamp) as access_date,
                gate_id,
                COUNT(*) as total_attempts,
                SUM(CASE WHEN access_granted = 1 THEN 1 ELSE 0 END) as granted_count,
                SUM(CASE WHEN access_granted = 0 THEN 1 ELSE 0 END) as denied_count,
                SUM(CASE WHEN alert_triggered = 1 THEN 1 ELSE 0 END) as alert_count,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT license_plate) as unique_vehicles
            FROM access_logs
            WHERE timestamp >= :start_date
            GROUP BY DATE(timestamp), gate_id
            ORDER BY access_date DESC, gate_id
        """)
        
        result = self.db.execute(query, {"start_date": start_date}).fetchall()
        
        return [
            {
                "date": row.access_date.isoformat() if row.access_date else None,
                "gate_id": row.gate_id,
                "total_attempts": row.total_attempts,
                "granted_count": row.granted_count,
                "denied_count": row.denied_count,
                "alert_count": row.alert_count,
                "unique_users": row.unique_users,
                "unique_vehicles": row.unique_vehicles
            }
            for row in result
        ]
    
    def search_logs(self, search_term: str, limit: int = 50, skip: int = 0) -> List[AccessLog]:
        """Search logs by user ID, license plate, or notes"""
        search_pattern = f"%{search_term}%"
        
        return self.db.query(AccessLog)\
            .options(joinedload(AccessLog.user), joinedload(AccessLog.vehicle))\
            .filter(
                or_(
                    AccessLog.user_id.ilike(search_pattern),
                    AccessLog.license_plate.ilike(search_pattern),
                    AccessLog.notes.ilike(search_pattern),
                    AccessLog.gate_id.ilike(search_pattern)
                )
            )\
            .order_by(desc(AccessLog.timestamp))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """Clean up old access logs"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        deleted_count = self.db.query(AccessLog)\
            .filter(AccessLog.timestamp < cutoff_date)\
            .delete()
        
        self.db.commit()
        return deleted_count