"""
User repository for database operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.user import User, UserRole, UserStatus
from .base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations
    """
    
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_active_user(self, user_id: str) -> Optional[User]:
        """Get active user by ID"""
        return self.db.query(User).filter(
            and_(User.id == user_id, User.status == UserStatus.ACTIVE)
        ).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role"""
        return self.db.query(User).filter(User.role == role).offset(skip).limit(limit).all()
    
    def get_by_department(self, department: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by department"""
        return self.db.query(User).filter(User.department == department).offset(skip).limit(limit).all()
    
    def search_users(self, search_term: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by name or email"""
        search_pattern = f"%{search_term}%"
        return self.db.query(User).filter(
            or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.id.ilike(search_pattern)
            )
        ).offset(skip).limit(limit).all()
    
    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        return self.db.query(User).filter(User.status == UserStatus.ACTIVE).offset(skip).limit(limit).all()
    
    def verify_user_id(self, user_id: str) -> dict:
        """
        Verify if user ID is valid and active
        Returns verification result with user details
        """
        user = self.get_active_user(user_id)
        
        if user:
            return {
                "is_valid": True,
                "user_id": user.id,
                "name": user.name,
                "role": user.role.value,
                "department": user.department,
                "status": user.status.value
            }
        else:
            return {
                "is_valid": False,
                "user_id": user_id,
                "name": None,
                "role": None,
                "department": None,
                "status": None
            }
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user"""
        user = self.get_by_id(user_id)
        if user:
            user.status = UserStatus.INACTIVE
            self.db.commit()
            return True
        return False
    
    def activate_user(self, user_id: str) -> bool:
        """Activate a user"""
        user = self.get_by_id(user_id)
        if user:
            user.status = UserStatus.ACTIVE
            self.db.commit()
            return True
        return False
    
    def get_user_statistics(self) -> dict:
        """Get user statistics"""
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.status == UserStatus.ACTIVE).count()
        
        # Count by role
        students = self.db.query(User).filter(User.role == UserRole.STUDENT).count()
        staff = self.db.query(User).filter(User.role == UserRole.STAFF).count()
        faculty = self.db.query(User).filter(User.role == UserRole.FACULTY).count()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "by_role": {
                "students": students,
                "staff": staff,
                "faculty": faculty
            }
        }
    
    def create_user(self, user_data: dict) -> User:
        """Create a new user with validation"""
        # Check if user ID already exists
        existing_user = self.get_by_id(user_data.get("id"))
        if existing_user:
            raise ValueError(f"User with ID {user_data.get('id')} already exists")
        
        # Check if email already exists
        if user_data.get("email"):
            existing_email = self.get_by_email(user_data.get("email"))
            if existing_email:
                raise ValueError(f"User with email {user_data.get('email')} already exists")
        
        # Create user
        user = User.create_from_dict(user_data)
        return self.create_from_model(user)