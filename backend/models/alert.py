"""
Alert model for Smart Campus Access Control
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from database.connection import Base
import enum
from sqlalchemy import Enum

class AlertType(enum.Enum):
    UNAUTHORIZED_ID = "unauthorized_id"
    UNAUTHORIZED_VEHICLE = "unauthorized_vehicle"
    SYSTEM_ERROR = "system_error"

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_type = Column(Enum(AlertType), nullable=False, index=True)
    message = Column(Text, nullable=False)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"))
    license_plate = Column(String(20), ForeignKey("vehicles.license_plate", ondelete="SET NULL"))
    gate_id = Column(String(10), default="MAIN_GATE", index=True)
    resolved = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    vehicle = relationship("Vehicle", back_populates="alerts")
    
    def __repr__(self):
        status = "RESOLVED" if self.resolved else "ACTIVE"
        return f"<Alert(id={self.id}, type='{self.alert_type.value}', status='{status}')>"
    
    def to_dict(self):
        """Convert alert object to dictionary"""
        return {
            "id": self.id,
            "alert_type": self.alert_type.value if self.alert_type else None,
            "message": self.message,
            "user_id": self.user_id,
            "license_plate": self.license_plate,
            "gate_id": self.gate_id,
            "resolved": self.resolved,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            # Include related data
            "user_name": self.user.name if self.user else None,
            "user_role": self.user.role.value if self.user and self.user.role else None,
            "vehicle_owner": self.vehicle.owner.name if self.vehicle and self.vehicle.owner else None,
            "vehicle_type": self.vehicle.vehicle_type.value if self.vehicle and self.vehicle.vehicle_type else None
        }
    
    @property
    def type_text(self):
        """Get human-readable alert type"""
        type_map = {
            AlertType.UNAUTHORIZED_ID: "Unauthorized ID",
            AlertType.UNAUTHORIZED_VEHICLE: "Unauthorized Vehicle",
            AlertType.SYSTEM_ERROR: "System Error"
        }
        return type_map.get(self.alert_type, "Unknown")
    
    @property
    def is_active(self):
        """Check if alert is still active"""
        return not self.resolved
    
    @property
    def age_minutes(self):
        """Get alert age in minutes"""
        if self.created_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            delta = now - self.created_at.replace(tzinfo=timezone.utc)
            return int(delta.total_seconds() / 60)
        return 0
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = func.now()
    
    @classmethod
    def create_from_dict(cls, data):
        """Create alert from dictionary data"""
        return cls(
            alert_type=AlertType(data.get("alert_type")) if data.get("alert_type") else None,
            message=data.get("message"),
            user_id=data.get("user_id"),
            license_plate=data.get("license_plate"),
            gate_id=data.get("gate_id", "MAIN_GATE"),
            resolved=data.get("resolved", False)
        )
    
    @classmethod
    def create_unauthorized_id_alert(cls, user_id, gate_id="MAIN_GATE"):
        """Create unauthorized ID alert"""
        message = f"Unauthorized ID scan attempt detected - ID: {user_id}"
        return cls(
            alert_type=AlertType.UNAUTHORIZED_ID,
            message=message,
            user_id=user_id,
            gate_id=gate_id
        )
    
    @classmethod
    def create_unauthorized_vehicle_alert(cls, license_plate, gate_id="MAIN_GATE"):
        """Create unauthorized vehicle alert"""
        message = f"Unregistered vehicle detected - Plate: {license_plate}"
        return cls(
            alert_type=AlertType.UNAUTHORIZED_VEHICLE,
            message=message,
            license_plate=license_plate,
            gate_id=gate_id
        )
    
    @classmethod
    def create_system_error_alert(cls, error_message, gate_id="MAIN_GATE"):
        """Create system error alert"""
        return cls(
            alert_type=AlertType.SYSTEM_ERROR,
            message=f"System error: {error_message}",
            gate_id=gate_id
        )