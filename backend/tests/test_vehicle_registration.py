#!/usr/bin/env python3
"""
Comprehensive tests for vehicle registration endpoint
"""

import pytest
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base, get_db
from main import app
from models import User, Vehicle, UserRole, UserStatus, VehicleType, VehicleStatus
from services.vehicle_service import VehicleService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_vehicles.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestVehicleRegistration:
    """Test suite for vehicle registration functionality"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database and client"""
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.setup_test_data()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database"""
        Base.metadata.drop_all(bind=engine)
    
    @classmethod
    def setup_test_data(cls):
        """Create test users"""
        db = TestingSessionLocal()
        
        # Create test users
        test_users = [
            User(
                id="STU001",
                name="John Doe",
                email="john@test.edu",
                role=UserRole.STUDENT,
                department="Computer Science",
                status=UserStatus.ACTIVE
            ),
            User(
                id="STU002",
                name="Jane Smith",
                email="jane@test.edu",
                role=UserRole.STUDENT,
                department="Engineering",
                status=UserStatus.INACTIVE
            ),
            User(
                id="STF001",
                name="Bob Wilson",
                email="bob@test.edu",
                role=UserRole.STAFF,
                department="Administration",
                status=UserStatus.ACTIVE
            ),
            User(
                id="FAC001",
                name="Dr. Alice Brown",
                email="alice@test.edu",
                role=UserRole.FACULTY,
                department="Physics",
                status=UserStatus.ACTIVE
            )
        ]
        
        for user in test_users:
            db.add(user)
        
        db.commit()
        db.close()
    
    def test_valid_vehicle_registration(self):
        """Test successful vehicle registration"""
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "TEST123",
                "owner_id": "STU001",
                "vehicle_type": "car",
                "color": "Blue",
                "model": "Honda Civic"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "Vehicle registered successfully" in data["message"]
        assert data["vehicle"]["license_plate"] == "TEST123"
        assert data["vehicle"]["owner_id"] == "STU001"
        assert data["vehicle"]["vehicle_type"] == "car"
        assert data["vehicle"]["color"] == "Blue"
        assert data["vehicle"]["model"] == "Honda Civic"
        assert "registration_timestamp" in data
    
    def test_duplicate_license_plate(self):
        """Test registration with duplicate license plate"""
        # First registration
        self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "DUP123",
                "owner_id": "STU001",
                "vehicle_type": "car"
            }
        )
        
        # Attempt duplicate registration
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "DUP123",
                "owner_id": "STF001",
                "vehicle_type": "motorcycle"
            }
        )
        
        assert response.status_code == 409  # Conflict
        data = response.json()
        
        assert "already exists" in data["detail"]["error"]
        assert data["detail"]["error_code"] == "DUPLICATE_LICENSE_PLATE"
        assert "existing_vehicle" in data["detail"]["details"]
    
    def test_invalid_owner(self):
        """Test registration with non-existent owner"""
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "NOOWNER",
                "owner_id": "INVALID999",
                "vehicle_type": "car"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "not found" in data["detail"]["error"]
        assert data["detail"]["error_code"] == "OWNER_NOT_FOUND"
    
    def test_inactive_owner(self):
        """Test registration with inactive owner"""
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "INACTIVE",
                "owner_id": "STU002",  # Inactive user
                "vehicle_type": "bicycle"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "inactive" in data["detail"]["error"]
        assert data["detail"]["error_code"] == "INACTIVE_OWNER"
    
    def test_invalid_vehicle_type(self):
        """Test registration with invalid vehicle type"""
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "INVALID",
                "owner_id": "STU001",
                "vehicle_type": "airplane"  # Invalid type
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_license_plate_format(self):
        """Test registration with invalid license plate formats"""
        invalid_plates = ["", "AB", "TESTFAKEDEMOINVALID", "!!!"]
        
        for plate in invalid_plates:
            response = self.client.post(
                "/api/vehicles/register",
                json={
                    "license_plate": plate,
                    "owner_id": "STU001",
                    "vehicle_type": "car"
                }
            )
            
            # Should either be validation error (422) or bad request (400)
            assert response.status_code in [400, 422]
    
    def test_vehicle_limit_enforcement(self):
        """Test vehicle registration limits per user role"""
        # Register maximum vehicles for a student (limit: 2)
        for i in range(2):
            response = self.client.post(
                "/api/vehicles/register",
                json={
                    "license_plate": f"LIMIT{i}",
                    "owner_id": "STU001",
                    "vehicle_type": "car"
                }
            )
            assert response.status_code == 200
        
        # Try to register one more (should fail)
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "EXCEED",
                "owner_id": "STU001",
                "vehicle_type": "motorcycle"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "limit exceeded" in data["detail"]["error"].lower()
        assert data["detail"]["error_code"] == "VEHICLE_LIMIT_EXCEEDED"
    
    def test_case_insensitive_handling(self):
        """Test that license plates are handled case-insensitively"""
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "case123",  # lowercase
                "owner_id": "stf001",        # lowercase
                "vehicle_type": "car"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should be converted to uppercase
        assert data["vehicle"]["license_plate"] == "CASE123"
        assert data["vehicle"]["owner_id"] == "STF001"
    
    def test_optional_fields(self):
        """Test registration with and without optional fields"""
        # Without optional fields
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "MINIMAL",
                "owner_id": "STF001",
                "vehicle_type": "bicycle"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["vehicle"]["color"] is None
        assert data["vehicle"]["model"] is None
        
        # With optional fields
        response = self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "FULL123",
                "owner_id": "STF001",
                "vehicle_type": "motorcycle",
                "color": "Red",
                "model": "Yamaha R15"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["vehicle"]["color"] == "Red"
        assert data["vehicle"]["model"] == "Yamaha R15"
    
    def test_vehicle_update(self):
        """Test vehicle information update"""
        # First register a vehicle
        self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "UPDATE1",
                "owner_id": "STF001",
                "vehicle_type": "car",
                "color": "Blue"
            }
        )
        
        # Update the vehicle
        response = self.client.put(
            "/api/vehicles/UPDATE1",
            json={
                "color": "Red",
                "model": "Toyota Camry"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["vehicle"]["color"] == "Red"
        assert data["vehicle"]["model"] == "Toyota Camry"
    
    def test_ownership_transfer(self):
        """Test vehicle ownership transfer"""
        # Register a vehicle
        self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "TRANSFER",
                "owner_id": "STU001",
                "vehicle_type": "car"
            }
        )
        
        # Transfer ownership
        response = self.client.post(
            "/api/vehicles/TRANSFER/transfer",
            json={
                "new_owner_id": "STF001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transferred" in data["message"]
        assert data["new_owner"]["owner_id"] == "STF001"
    
    def test_get_vehicle_info(self):
        """Test getting vehicle information"""
        # Register a vehicle
        self.client.post(
            "/api/vehicles/register",
            json={
                "license_plate": "INFO123",
                "owner_id": "STF001",
                "vehicle_type": "car",
                "color": "Green",
                "model": "Honda Accord"
            }
        )
        
        # Get vehicle info
        response = self.client.get("/api/vehicles/INFO123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["vehicle"]["license_plate"] == "INFO123"
        assert data["vehicle"]["color"] == "Green"
        assert data["vehicle"]["model"] == "Honda Accord"
    
    def test_list_vehicles(self):
        """Test listing vehicles with filters"""
        # List all vehicles
        response = self.client.get("/api/vehicles/?limit=50")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "vehicles" in data
        assert "total" in data
        assert isinstance(data["vehicles"], list)
        
        # List vehicles by owner
        response = self.client.get("/api/vehicles/?owner_id=STF001")
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned vehicles should belong to STF001
        for vehicle in data["vehicles"]:
            assert vehicle["owner_id"] == "STF001"
    
    def test_get_owner_vehicles(self):
        """Test getting all vehicles for a specific owner"""
        response = self.client.get("/api/vehicles/owner/STF001")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["owner_id"] == "STF001"
        assert "vehicles" in data
        assert "total" in data
    
    def test_registration_statistics(self):
        """Test getting registration statistics"""
        response = self.client.get("/api/vehicles/statistics/registration")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_statistics" in data
        assert "recent_registrations" in data
        assert "limits_by_role" in data

class TestVehicleService:
    """Test suite for VehicleService class"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database"""
        Base.metadata.create_all(bind=engine)
        cls.setup_test_data()
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database"""
        Base.metadata.drop_all(bind=engine)
    
    @classmethod
    def setup_test_data(cls):
        """Create test users"""
        db = TestingSessionLocal()
        
        user = User(
            id="SVCTEST",
            name="Service Test User",
            email="service@test.edu",
            role=UserRole.STUDENT,
            department="Test Department",
            status=UserStatus.ACTIVE
        )
        
        db.add(user)
        db.commit()
        db.close()
    
    def test_license_plate_validation(self):
        """Test license plate format validation"""
        db = TestingSessionLocal()
        service = VehicleService(db)
        
        # Valid plates
        valid_plates = ["ABC123", "XYZ789", "TEST-1", "CAR001"]
        for plate in valid_plates:
            assert service._is_valid_license_plate(plate) is True
        
        # Invalid plates
        invalid_plates = ["", "AB", "TESTFAKEDEMOINVALID", "!!!", "AAAA", "TEST"]
        for plate in invalid_plates:
            assert service._is_valid_license_plate(plate) is False
        
        db.close()
    
    def test_vehicle_limits(self):
        """Test vehicle limit calculation by role"""
        db = TestingSessionLocal()
        service = VehicleService(db)
        
        # Test limits for different roles
        assert service._get_vehicle_limit(UserRole.STUDENT) == 2
        assert service._get_vehicle_limit(UserRole.STAFF) == 3
        assert service._get_vehicle_limit(UserRole.FACULTY) == 5
        
        db.close()
    
    def test_vehicle_data_validation(self):
        """Test vehicle data validation"""
        db = TestingSessionLocal()
        service = VehicleService(db)
        
        # Valid data
        valid_data = {
            "license_plate": "VALID123",
            "owner_id": "SVCTEST",
            "vehicle_type": "car",
            "color": "Blue",
            "model": "Test Car"
        }
        
        result = service._validate_vehicle_data(valid_data)
        assert result["valid"] is True
        assert result["data"]["license_plate"] == "VALID123"
        
        # Invalid data - missing required field
        invalid_data = {
            "license_plate": "INVALID",
            # Missing owner_id and vehicle_type
        }
        
        result = service._validate_vehicle_data(invalid_data)
        assert result["valid"] is False
        assert result["error_code"] == "MISSING_REQUIRED_FIELD"
        
        db.close()

def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    run_tests()