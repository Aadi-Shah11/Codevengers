#!/usr/bin/env python3
"""
Comprehensive tests for ID verification endpoint
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import Base, get_db
from main import app
from models import User, UserRole, UserStatus
from services.verification_service import VerificationService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestIDVerification:
    """Test suite for ID verification functionality"""
    
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
            )
        ]
        
        for user in test_users:
            db.add(user)
        
        db.commit()
        db.close()
    
    def test_valid_id_verification(self):
        """Test successful ID verification"""
        response = self.client.post(
            "/api/auth/verify_id",
            json={
                "id_number": "STU001",
                "scan_method": "manual"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is True
        assert data["user_id"] == "STU001"
        assert data["user_name"] == "John Doe"
        assert data["user_role"] == "student"
        assert data["verification_method"] == "id_only"
        assert "timestamp" in data
        assert "log_id" in data
    
    def test_invalid_id_verification(self):
        """Test ID verification with non-existent user"""
        response = self.client.post(
            "/api/auth/verify_id",
            json={
                "id_number": "INVALID999",
                "scan_method": "manual"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is False
        assert data["user_id"] == "INVALID999"
        assert "Access denied" in data["message"]
        assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_inactive_user_verification(self):
        """Test ID verification with inactive user"""
        response = self.client.post(
            "/api/auth/verify_id",
            json={
                "id_number": "STU002",
                "scan_method": "qr"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is False
        assert data["user_id"] == "STU002"
        assert data["user_name"] == "Jane Smith"
        assert data["error_code"] == "INACTIVE_USER"
    
    def test_empty_id_verification(self):
        """Test ID verification with empty ID"""
        response = self.client.post(
            "/api/auth/verify_id",
            json={
                "id_number": "",
                "scan_method": "manual"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_suspicious_id_patterns(self):
        """Test detection of suspicious ID patterns"""
        suspicious_ids = ["TEST123", "HACK001", "ADMIN999", "AAAA", "1234"]
        
        for suspicious_id in suspicious_ids:
            response = self.client.post(
                "/api/auth/verify_id",
                json={
                    "id_number": suspicious_id,
                    "scan_method": "manual"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_granted"] is False
            assert data["error_code"] == "SUSPICIOUS_PATTERN"
    
    def test_different_scan_methods(self):
        """Test different scan methods"""
        scan_methods = ["qr", "barcode", "manual"]
        
        for method in scan_methods:
            response = self.client.post(
                "/api/auth/verify_id",
                json={
                    "id_number": "STU001",
                    "scan_method": method
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["access_granted"] is True
            assert data["scan_method"] == method
    
    def test_case_insensitive_id(self):
        """Test that ID verification is case insensitive"""
        response = self.client.post(
            "/api/auth/verify_id",
            json={
                "id_number": "stu001",  # lowercase
                "scan_method": "manual"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["user_name"] == "John Doe"
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled"""
        response = self.client.post(
            "/api/auth/verify_id",
            json={
                "id_number": "  STU001  ",  # with whitespace
                "scan_method": "manual"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["user_id"] == "STU001"  # Should be trimmed
    
    def test_get_user_info(self):
        """Test getting user information"""
        response = self.client.get("/api/auth/user/STU001")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == "STU001"
        assert data["name"] == "John Doe"
        assert data["role"] == "student"
        assert "vehicles" in data
        assert "recent_access" in data
    
    def test_list_users(self):
        """Test listing users"""
        response = self.client.get("/api/auth/users?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "users" in data
        assert "total" in data
        assert len(data["users"]) <= 10
    
    def test_user_validation(self):
        """Test user ID format validation"""
        # Valid ID
        response = self.client.get("/api/auth/validate/STU001")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        
        # Invalid ID (too short)
        response = self.client.get("/api/auth/validate/AB")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["error_code"] == "INVALID_LENGTH"
    
    def test_verification_statistics(self):
        """Test getting verification statistics"""
        response = self.client.get("/api/auth/verification/statistics?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_days" in data
        assert "access_statistics" in data
        assert "verification_methods" in data
        assert "security_levels" in data
    
    def test_comprehensive_access_verification(self):
        """Test the comprehensive access verification endpoint"""
        response = self.client.post(
            "/api/auth/verify_access?user_id=STU001&gate_id=MAIN_GATE"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is True
        assert data["verification_method"] == "id_only"
        assert data["security_level"] in ["LOW_RISK", "MEDIUM_RISK", "HIGH_RISK"]
        assert "decision_reason" in data
        assert "user_verification" in data

class TestVerificationService:
    """Test suite for VerificationService class"""
    
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
            id="TEST001",
            name="Test User",
            email="test@test.edu",
            role=UserRole.STUDENT,
            department="Test Department",
            status=UserStatus.ACTIVE
        )
        
        db.add(user)
        db.commit()
        db.close()
    
    def test_verify_user_id_service(self):
        """Test VerificationService.verify_user_id method"""
        db = TestingSessionLocal()
        service = VerificationService(db)
        
        # Valid user
        result = service.verify_user_id("TEST001")
        assert result["is_valid"] is True
        assert result["user_name"] == "Test User"
        
        # Invalid user
        result = service.verify_user_id("INVALID999")
        assert result["is_valid"] is False
        assert result["error_code"] == "USER_NOT_FOUND"
        
        # Empty ID
        result = service.verify_user_id("")
        assert result["is_valid"] is False
        assert result["error_code"] == "EMPTY_ID"
        
        # Suspicious ID
        result = service.verify_user_id("HACK123")
        assert result["is_valid"] is False
        assert result["error_code"] == "SUSPICIOUS_PATTERN"
        
        db.close()
    
    def test_suspicious_id_detection(self):
        """Test suspicious ID pattern detection"""
        db = TestingSessionLocal()
        service = VerificationService(db)
        
        # Test various suspicious patterns
        suspicious_patterns = [
            "TEST123", "DEMO001", "ADMIN999", "HACK001",
            "AAAA", "1111", "BBBB", "9999",
            "1234", "ABCD"  # Sequential patterns
        ]
        
        for pattern in suspicious_patterns:
            assert service._is_suspicious_id(pattern) is True
        
        # Test valid patterns
        valid_patterns = ["STU001", "FAC123", "STF456", "USER789"]
        
        for pattern in valid_patterns:
            assert service._is_suspicious_id(pattern) is False
        
        db.close()

def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    run_tests()