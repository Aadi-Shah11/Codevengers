"""
Vehicle repository for database operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from models.vehicle import Vehicle, VehicleType, VehicleStatus
from models.user import User
from .base_repository import BaseRepository

class VehicleRepository(BaseRepository[Vehicle]):
    """
    Repository for Vehicle model operations
    """
    
    def __init__(self, db: Session):
        super().__init__(Vehicle, db)
    
    def get_by_license_plate(self, license_plate: str) -> Optional[Vehicle]:
        """Get vehicle by license plate"""
        return self.db.query(Vehicle).filter(Vehicle.license_plate == license_plate).first()
    
    def get_active_vehicle(self, license_plate: str) -> Optional[Vehicle]:
        """Get active vehicle by license plate"""
        return self.db.query(Vehicle).filter(
            and_(Vehicle.license_plate == license_plate, Vehicle.status == VehicleStatus.ACTIVE)
        ).first()
    
    def get_by_owner(self, owner_id: str, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Get vehicles by owner ID"""
        return self.db.query(Vehicle).filter(Vehicle.owner_id == owner_id).offset(skip).limit(limit).all()
    
    def get_by_type(self, vehicle_type: VehicleType, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Get vehicles by type"""
        return self.db.query(Vehicle).filter(Vehicle.vehicle_type == vehicle_type).offset(skip).limit(limit).all()
    
    def get_with_owner_details(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Get vehicles with owner information"""
        return self.db.query(Vehicle).options(joinedload(Vehicle.owner)).offset(skip).limit(limit).all()
    
    def search_vehicles(self, search_term: str, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Search vehicles by license plate, color, or model"""
        search_pattern = f"%{search_term}%"
        return self.db.query(Vehicle).filter(
            Vehicle.license_plate.ilike(search_pattern) |
            Vehicle.color.ilike(search_pattern) |
            Vehicle.model.ilike(search_pattern)
        ).offset(skip).limit(limit).all()
    
    def get_active_vehicles(self, skip: int = 0, limit: int = 100) -> List[Vehicle]:
        """Get all active vehicles"""
        return self.db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ACTIVE).offset(skip).limit(limit).all()
    
    def verify_vehicle(self, license_plate: str) -> dict:
        """
        Verify if vehicle is registered and active
        Returns verification result with vehicle and owner details
        """
        vehicle = self.db.query(Vehicle).options(joinedload(Vehicle.owner)).filter(
            and_(Vehicle.license_plate == license_plate, Vehicle.status == VehicleStatus.ACTIVE)
        ).first()
        
        if vehicle:
            return {
                "is_valid": True,
                "license_plate": vehicle.license_plate,
                "vehicle_type": vehicle.vehicle_type.value,
                "color": vehicle.color,
                "model": vehicle.model,
                "owner_id": vehicle.owner_id,
                "owner_name": vehicle.owner.name if vehicle.owner else None,
                "status": vehicle.status.value
            }
        else:
            return {
                "is_valid": False,
                "license_plate": license_plate,
                "vehicle_type": None,
                "color": None,
                "model": None,
                "owner_id": None,
                "owner_name": None,
                "status": None
            }
    
    def register_vehicle(self, vehicle_data: dict) -> Vehicle:
        """Register a new vehicle with validation"""
        license_plate = vehicle_data.get("license_plate")
        
        # Check if license plate already exists
        existing_vehicle = self.get_by_license_plate(license_plate)
        if existing_vehicle:
            raise ValueError(f"Vehicle with license plate {license_plate} already exists")
        
        # Verify owner exists
        owner_id = vehicle_data.get("owner_id")
        if owner_id:
            owner = self.db.query(User).filter(User.id == owner_id).first()
            if not owner:
                raise ValueError(f"Owner with ID {owner_id} not found")
        
        # Create vehicle
        vehicle = Vehicle.create_from_dict(vehicle_data)
        return self.create_from_model(vehicle)
    
    def deactivate_vehicle(self, license_plate: str) -> bool:
        """Deactivate a vehicle"""
        vehicle = self.get_by_license_plate(license_plate)
        if vehicle:
            vehicle.status = VehicleStatus.INACTIVE
            self.db.commit()
            return True
        return False
    
    def activate_vehicle(self, license_plate: str) -> bool:
        """Activate a vehicle"""
        vehicle = self.get_by_license_plate(license_plate)
        if vehicle:
            vehicle.status = VehicleStatus.ACTIVE
            self.db.commit()
            return True
        return False
    
    def transfer_ownership(self, license_plate: str, new_owner_id: str) -> bool:
        """Transfer vehicle ownership"""
        vehicle = self.get_by_license_plate(license_plate)
        if not vehicle:
            return False
        
        # Verify new owner exists
        new_owner = self.db.query(User).filter(User.id == new_owner_id).first()
        if not new_owner:
            raise ValueError(f"New owner with ID {new_owner_id} not found")
        
        vehicle.owner_id = new_owner_id
        self.db.commit()
        return True
    
    def get_vehicle_statistics(self) -> dict:
        """Get vehicle statistics"""
        total_vehicles = self.db.query(Vehicle).count()
        active_vehicles = self.db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ACTIVE).count()
        
        # Count by type
        cars = self.db.query(Vehicle).filter(Vehicle.vehicle_type == VehicleType.CAR).count()
        motorcycles = self.db.query(Vehicle).filter(Vehicle.vehicle_type == VehicleType.MOTORCYCLE).count()
        bicycles = self.db.query(Vehicle).filter(Vehicle.vehicle_type == VehicleType.BICYCLE).count()
        
        return {
            "total_vehicles": total_vehicles,
            "active_vehicles": active_vehicles,
            "inactive_vehicles": total_vehicles - active_vehicles,
            "by_type": {
                "cars": cars,
                "motorcycles": motorcycles,
                "bicycles": bicycles
            }
        }
    
    def get_owner_vehicles(self, owner_id: str) -> List[Vehicle]:
        """Get all vehicles owned by a specific user"""
        return self.db.query(Vehicle).filter(Vehicle.owner_id == owner_id).all()