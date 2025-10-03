"""
Alert repository for database operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from models.alert import Alert, AlertType
from .base_repository import BaseRepository

class AlertRepository(BaseRepository[Alert]):
    """
    Repository for Alert model operations
    """
    
    def __init__(self, db: Session):
        super().__init__(Alert, db)
    
    def get_active_alerts(self, limit: int = 50, skip: int = 0) -> List[Alert]:
        """Get active (unresolved) alerts"""
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(Alert.resolved == False)\
            .order_by(desc(Alert.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_recent_alerts(self, hours: int = 24, limit: int = 50, skip: int = 0) -> List[Alert]:
        """Get recent alerts within specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(Alert.created_at >= cutoff_time)\
            .order_by(desc(Alert.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_alerts_by_type(self, alert_type: AlertType, limit: int = 50, skip: int = 0) -> List[Alert]:
        """Get alerts by type"""
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(Alert.alert_type == alert_type)\
            .order_by(desc(Alert.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_alerts_by_gate(self, gate_id: str, limit: int = 50, skip: int = 0) -> List[Alert]:
        """Get alerts for specific gate"""
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(Alert.gate_id == gate_id)\
            .order_by(desc(Alert.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_alerts_by_user(self, user_id: str, limit: int = 50, skip: int = 0) -> List[Alert]:
        """Get alerts related to specific user"""
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(Alert.user_id == user_id)\
            .order_by(desc(Alert.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_alerts_by_vehicle(self, license_plate: str, limit: int = 50, skip: int = 0) -> List[Alert]:
        """Get alerts related to specific vehicle"""
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(Alert.license_plate == license_plate)\
            .order_by(desc(Alert.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def create_unauthorized_id_alert(self, user_id: str, gate_id: str = "MAIN_GATE") -> Alert:
        """Create unauthorized ID alert"""
        alert = Alert.create_unauthorized_id_alert(user_id, gate_id)
        return self.create_from_model(alert)
    
    def create_unauthorized_vehicle_alert(self, license_plate: str, gate_id: str = "MAIN_GATE") -> Alert:
        """Create unauthorized vehicle alert"""
        alert = Alert.create_unauthorized_vehicle_alert(license_plate, gate_id)
        return self.create_from_model(alert)
    
    def create_system_error_alert(self, error_message: str, gate_id: str = "MAIN_GATE") -> Alert:
        """Create system error alert"""
        alert = Alert.create_system_error_alert(error_message, gate_id)
        return self.create_from_model(alert)
    
    def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert"""
        alert = self.get_by_id(alert_id)
        if alert and not alert.resolved:
            alert.resolve()
            self.db.commit()
            return True
        return False
    
    def resolve_alerts_by_user(self, user_id: str) -> int:
        """Resolve all alerts for a specific user"""
        alerts = self.db.query(Alert)\
            .filter(and_(Alert.user_id == user_id, Alert.resolved == False))\
            .all()
        
        count = 0
        for alert in alerts:
            alert.resolve()
            count += 1
        
        if count > 0:
            self.db.commit()
        
        return count
    
    def resolve_alerts_by_vehicle(self, license_plate: str) -> int:
        """Resolve all alerts for a specific vehicle"""
        alerts = self.db.query(Alert)\
            .filter(and_(Alert.license_plate == license_plate, Alert.resolved == False))\
            .all()
        
        count = 0
        for alert in alerts:
            alert.resolve()
            count += 1
        
        if count > 0:
            self.db.commit()
        
        return count
    
    def get_alert_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get alert statistics for specified period"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Total alerts
        total_alerts = self.db.query(Alert).filter(Alert.created_at >= start_date).count()
        
        # Active alerts
        active_alerts = self.db.query(Alert)\
            .filter(and_(Alert.created_at >= start_date, Alert.resolved == False))\
            .count()
        
        # Resolved alerts
        resolved_alerts = self.db.query(Alert)\
            .filter(and_(Alert.created_at >= start_date, Alert.resolved == True))\
            .count()
        
        # Alerts by type
        unauthorized_id = self.db.query(Alert)\
            .filter(and_(Alert.created_at >= start_date, Alert.alert_type == AlertType.UNAUTHORIZED_ID))\
            .count()
        
        unauthorized_vehicle = self.db.query(Alert)\
            .filter(and_(Alert.created_at >= start_date, Alert.alert_type == AlertType.UNAUTHORIZED_VEHICLE))\
            .count()
        
        system_error = self.db.query(Alert)\
            .filter(and_(Alert.created_at >= start_date, Alert.alert_type == AlertType.SYSTEM_ERROR))\
            .count()
        
        # Resolution rate
        resolution_rate = (resolved_alerts / total_alerts * 100) if total_alerts > 0 else 0
        
        return {
            "period_days": days,
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "resolution_rate": round(resolution_rate, 2),
            "by_type": {
                "unauthorized_id": unauthorized_id,
                "unauthorized_vehicle": unauthorized_vehicle,
                "system_error": system_error
            }
        }
    
    def get_alert_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily alert trends"""
        start_date = datetime.now() - timedelta(days=days)
        
        # Group alerts by date
        results = self.db.query(
            func.date(Alert.created_at).label('alert_date'),
            func.count(Alert.id).label('total_count'),
            func.sum(func.case([(Alert.alert_type == AlertType.UNAUTHORIZED_ID, 1)], else_=0)).label('unauthorized_id_count'),
            func.sum(func.case([(Alert.alert_type == AlertType.UNAUTHORIZED_VEHICLE, 1)], else_=0)).label('unauthorized_vehicle_count'),
            func.sum(func.case([(Alert.alert_type == AlertType.SYSTEM_ERROR, 1)], else_=0)).label('system_error_count'),
            func.sum(func.case([(Alert.resolved == True, 1)], else_=0)).label('resolved_count')
        )\
        .filter(Alert.created_at >= start_date)\
        .group_by(func.date(Alert.created_at))\
        .order_by(func.date(Alert.created_at).desc())\
        .all()
        
        return [
            {
                "date": result.alert_date.isoformat() if result.alert_date else None,
                "total_alerts": result.total_count,
                "unauthorized_id": result.unauthorized_id_count,
                "unauthorized_vehicle": result.unauthorized_vehicle_count,
                "system_error": result.system_error_count,
                "resolved": result.resolved_count,
                "active": result.total_count - result.resolved_count
            }
            for result in results
        ]
    
    def search_alerts(self, search_term: str, limit: int = 50, skip: int = 0) -> List[Alert]:
        """Search alerts by message, user ID, or license plate"""
        search_pattern = f"%{search_term}%"
        
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(
                or_(
                    Alert.message.ilike(search_pattern),
                    Alert.user_id.ilike(search_pattern),
                    Alert.license_plate.ilike(search_pattern),
                    Alert.gate_id.ilike(search_pattern)
                )
            )\
            .order_by(desc(Alert.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def cleanup_old_alerts(self, days_to_keep: int = 90) -> int:
        """Clean up old resolved alerts"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        deleted_count = self.db.query(Alert)\
            .filter(and_(Alert.resolved == True, Alert.resolved_at < cutoff_date))\
            .delete()
        
        self.db.commit()
        return deleted_count
    
    def get_critical_alerts(self, limit: int = 10) -> List[Alert]:
        """Get most critical active alerts (recent unauthorized attempts)"""
        return self.db.query(Alert)\
            .options(joinedload(Alert.user), joinedload(Alert.vehicle))\
            .filter(
                and_(
                    Alert.resolved == False,
                    or_(
                        Alert.alert_type == AlertType.UNAUTHORIZED_ID,
                        Alert.alert_type == AlertType.UNAUTHORIZED_VEHICLE
                    )
                )
            )\
            .order_by(desc(Alert.created_at))\
            .limit(limit)\
            .all()