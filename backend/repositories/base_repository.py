"""
Base repository class with common CRUD operations
"""

from typing import Generic, TypeVar, Type, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database.connection import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Base repository class providing common database operations
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination"""
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        try:
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def create_from_model(self, obj: ModelType) -> ModelType:
        """Create a new record from model instance"""
        try:
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def update(self, id: Any, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update an existing record"""
        try:
            db_obj = self.get_by_id(id)
            if db_obj:
                for field, value in obj_data.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)
                self.db.commit()
                self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def delete(self, id: Any) -> bool:
        """Delete a record by ID"""
        try:
            db_obj = self.get_by_id(id)
            if db_obj:
                self.db.delete(db_obj)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def count(self) -> int:
        """Get total count of records"""
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def exists(self, id: Any) -> bool:
        """Check if record exists by ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def filter_by(self, **kwargs) -> List[ModelType]:
        """Filter records by given criteria"""
        try:
            query = self.db.query(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
            return query.all()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def get_first_by(self, **kwargs) -> Optional[ModelType]:
        """Get first record matching criteria"""
        try:
            query = self.db.query(self.model)
            for field, value in kwargs.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
            return query.first()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e