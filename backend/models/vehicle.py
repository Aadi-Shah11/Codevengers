"""
Vehicle model for Smart Campus Access Control
"""

from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database.connection import Base
import enum

class VehicleType(enum.Enum):
    CAR = "car"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"

class VehicleStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    license_plate = Column(String(20), primary_key=True, index=True)
    owner_id = Column(String(20), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    vehicle_type = Column(Enum(VehicleType), nullable=False, index=True)
    color = Column(String(30), index=True)
    model = Column(String(50))
    status = Column(Enum(VehicleStatus), default=VehicleStatus.ACTIVE, index=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="vehicles")
    access_logs = relationship("AccessLog", back_populates="vehicle")
    alerts = relationship("Alert", back_populates="vehicle")
    
    def __repr__(self):
        return f"<Vehicle(plate='{self.license_plate}', type='{self.vehicle_type.value}', owner='{self.owner_id}')>"
    
    def to_dict(self):
        """Convert vehicle object to dictionary"""
        return {
            "license_plate": self.license_plate,
            "owner_id": self.owner_id,
            "vehicle_type": self.vehicle_type.value if self.vehicle_type else None,
            "color": self.color,
            "model": self.model,
            "status": self.status.value if self.status else None,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "owner_name": self.owner.name if self.owner else None
        }
    
    @property
    def is_active(self):
        """Check if vehicle is active"""
        return self.status == VehicleStatus.ACTIVE
    
    @property
    def display_name(self):
        """Get display name for vehicle"""
        parts = [self.color, self.model, self.vehicle_type.value]
        return " ".join(filter(None, parts)).title()
    
    @classmethod
    def create_from_dict(cls, data):
        """Create vehicle from dictionary data"""
        return cls(
            license_plate=data.get("license_plate"),
            owner_id=data.get("owner_id"),
            vehicle_type=VehicleType(data.get("vehicle_type")) if data.get("vehicle_type") else None,
            color=data.get("color"),
            model=data.get("model"),
            status=VehicleStatus(data.get("status", "active"))
        )