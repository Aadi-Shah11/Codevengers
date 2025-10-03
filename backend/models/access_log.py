"""
Access Log model for Smart Campus Access Control
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from database.connection import Base
import enum
from sqlalchemy import Enum

class VerificationMethod(enum.Enum):
    ID_ONLY = "id_only"
    VEHICLE_ONLY = "vehicle_only"
    BOTH = "both"

class AccessLog(Base):
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    gate_id = Column(String(10), default="MAIN_GATE", index=True)
    user_id = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    license_plate = Column(String(20), ForeignKey("vehicles.license_plate", ondelete="SET NULL"), index=True)
    verification_method = Column(Enum(VerificationMethod), nullable=False)
    access_granted = Column(Boolean, nullable=False, index=True)
    alert_triggered = Column(Boolean, default=False, index=True)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="access_logs")
    vehicle = relationship("Vehicle", back_populates="access_logs")
    
    def __repr__(self):
        status = "GRANTED" if self.access_granted else "DENIED"
        return f"<AccessLog(id={self.id}, gate='{self.gate_id}', status='{status}')>"
    
    def to_dict(self):
        """Convert access log object to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "gate_id": self.gate_id,
            "user_id": self.user_id,
            "license_plate": self.license_plate,
            "verification_method": self.verification_method.value if self.verification_method else None,
            "access_granted": self.access_granted,
            "alert_triggered": self.alert_triggered,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # Include related data
            "user_name": self.user.name if self.user else None,
            "user_role": self.user.role.value if self.user and self.user.role else None,
            "vehicle_type": self.vehicle.vehicle_type.value if self.vehicle and self.vehicle.vehicle_type else None,
            "vehicle_color": self.vehicle.color if self.vehicle else None,
            "vehicle_model": self.vehicle.model if self.vehicle else None
        }
    
    @property
    def status_text(self):
        """Get human-readable status"""
        return "Access Granted" if self.access_granted else "Access Denied"
    
    @property
    def method_text(self):
        """Get human-readable verification method"""
        method_map = {
            VerificationMethod.ID_ONLY: "ID Only",
            VerificationMethod.VEHICLE_ONLY: "Vehicle Only",
            VerificationMethod.BOTH: "ID + Vehicle"
        }
        return method_map.get(self.verification_method, "Unknown")
    
    @classmethod
    def create_from_dict(cls, data):
        """Create access log from dictionary data"""
        return cls(
            gate_id=data.get("gate_id", "MAIN_GATE"),
            user_id=data.get("user_id"),
            license_plate=data.get("license_plate"),
            verification_method=VerificationMethod(data.get("verification_method")) if data.get("verification_method") else None,
            access_granted=data.get("access_granted", False),
            alert_triggered=data.get("alert_triggered", False),
            notes=data.get("notes")
        )
    
    @classmethod
    def log_access_attempt(cls, gate_id, user_id=None, license_plate=None, 
                          verification_method=None, access_granted=False, notes=None):
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
        
        # Trigger alert if access denied
        alert_triggered = not access_granted
        
        return cls(
            gate_id=gate_id,
            user_id=user_id,
            license_plate=license_plate,
            verification_method=verification_method,
            access_granted=access_granted,
            alert_triggered=alert_triggered,
            notes=notes
        )