"""
User model for Smart Campus Access Control
"""

from sqlalchemy import Column, String, Enum, DateTime, func
from sqlalchemy.orm import relationship
from database.connection import Base
import enum

class UserRole(enum.Enum):
    STUDENT = "student"
    STAFF = "staff"
    FACULTY = "faculty"

class UserStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(20), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), index=True)
    role = Column(Enum(UserRole), nullable=False, index=True)
    department = Column(String(50), index=True)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="user")
    alerts = relationship("Alert", back_populates="user")
    
    def __repr__(self):
        return f"<User(id='{self.id}', name='{self.name}', role='{self.role.value}')>"
    
    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value if self.role else None,
            "department": self.department,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @property
    def is_active(self):
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE
    
    @classmethod
    def create_from_dict(cls, data):
        """Create user from dictionary data"""
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            role=UserRole(data.get("role")) if data.get("role") else None,
            department=data.get("department"),
            status=UserStatus(data.get("status", "active"))
        )