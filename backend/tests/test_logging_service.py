#!/usr/bin/env python3
"""
Comprehensive tests for logging service
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
from models import User, Vehicle, AccessLog, Alert, UserRole, UserStatus, VehicleType, VehicleStatus, VerificationMethod
from services.logging_service import LoggingService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_logging.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestLoggingService:
    """Test suite for LoggingService functionality"""
    
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
        """Create test data"""
        db = TestingSessionLocal()
        
        # Create test users
        test_users = [
            User(
                id="LOG001",
                name="Log Test User",
                email="log@test.edu",
                role=UserRole.STUDENT,
                department="Test Department",
                status=UserStatus.ACTIVE
            ),
            User(
                id="LOG002",
                name="Log Test Staff",
                email="staff@test.edu",
                role=UserRole.STAFF,
                department="Administration",
                status=UserStatus.ACTIVE
            )
        ]
        
        # Create test vehicles
        test_vehicles = [
            Vehicle(
                license_plate="LOG123",
                owner_id="LOG001",
                vehicle_type=VehicleType.CAR,
                color="Blue",
                model="Test Car",
                status=VehicleStatus.ACTIVE
            ),
            Vehicle(
                license_plate="LOG456",
                owner_id="LOG002",
                vehicle_type=VehicleType.MOTORCYCLE,
                color="Red",
                model="Test Bike",
                status=VehicleStatus.ACTIVE
            )
        ]
        
        for user in test_users:
            db.add(user)
        for vehicle in test_vehicles:
            db.add(vehicle)
        
        db.commit()
        db.close()
    
    def test_log_access_attempt(self):
        """Test logging access attempts"""
        db = TestingSessionLocal()
        logging_service = LoggingService(db)
        
        # Test successful access log
        result = logging_service.log_access_attempt(
            gate_id="TEST_GATE",
            user_id="LOG001",
            license_plate="LOG123",
            access_granted=True,
            notes="Test successful access"
        )
        
        assert result["success"] is True
        assert result["access_granted"] is True
        assert result["verification_method"] == "both"
        assert "log_id" in result
        assert "timestamp" in result
        
        # Test failed access log
        result = logging_service.log_access_attempt(
            gate_id="TEST_GATE",
            user_id="INVALID999",
            access_granted=False,
            notes="Test failed access"
        )
        
        assert result["success"] is True
        assert result["access_granted"] is False
        assert result["verification_method"] == "id_only"
        assert len(result["alert_ids"]) > 0  # Should generate alert
        
        db.close()
    
    def test_get_access_logs(self):
        """Test retrieving access logs with filters"""
        db = TestingSessionLocal()
        logging_service = LoggingService(db)
        
        # Create some test logs first
        for i in range(5):
            logging_service.log_access_attempt(
                gate_id="TEST_GATE",
                user_id="LOG001",
                access_granted=i % 2 == 0,  # Alternate success/failure
                notes=f"Test log {i}"
            )
        
        # Test getting all logs
        result = logging_service.get_access_logs()
        assert result["success"] is True
        assert len(result["logs"]) > 0
        
        # Test filtering by user
        filters = {"user_id": "LOG001"}
        result = logging_service.get_access_logs(filters)
        assert result["success"] is True
        for log in result["logs"]:
            assert log["user_id"] == "LOG001"
        
        # Test filtering by access result
        filters = {"access_granted": True}
        result = logging_service.get_access_logs(filters)
        assert result["success"] is True
        for log in result["logs"]:
            assert log["access_granted"] is True
        
        # Test pagination
        pagination = {"limit": 2, "offset": 0}
        result = logging_service.get_access_logs({}, pagination)
        assert result["success"] is True
        assert len(result["logs"]) <= 2
        
        db.close()
    
    def test_get_access_statistics(self):
        """Test access statistics generation"""
        db = TestingSessionLocal()
        logging_service = LoggingService(db)
        
        # Create test logs with different patterns
        base_time = datetime.now() - timedelta(days=1)
        
        for i in range(10):
            logging_service.log_access_attempt(
                gate_id="STATS_GATE",
                user_id="LOG001" if i % 2 == 0 else "LOG002",
                access_granted=i < 7,  # 7 successful, 3 failed
                notes=f"Stats test {i}"
            )
        
        # Get statistics
        result = logging_service.get_access_statistics(days=7, gate_id="STATS_GATE")
        
        assert result["success"] is True
        assert "basic_statistics" in result
        assert "verification_methods" in result
        assert "security_metrics" in result
        assert "top_entities" in result
        
        # Check basic statistics
        basic_stats = result["basic_statistics"]
        assert basic_stats["total_attempts"] >= 10
        assert basic_stats["granted_count"] >= 7
        assert basic_stats["denied_count"] >= 3
        
        # Check security metrics
        security_metrics = result["security_metrics"]
        assert "security_score" in security_metrics
        assert "threat_level" in security_metrics
        
        db.close()
    
    def test_get_audit_trail(self):
        """Test audit trail generation"""
        db = TestingSessionLocal()
        logging_service = LoggingService(db)
        
        # Create test logs for audit trail
        for i in range(3):
            logging_service.log_access_attempt(
                gate_id="AUDIT_GATE",
                user_id="LOG001",
                access_granted=True,
                notes=f"Audit test {i}"
            )
        
        # Get user audit trail
        result = logging_service.get_audit_trail("user", "LOG001", days=7)
        
        assert result["success"] is True
        assert result["entity_type"] == "user"
        assert result["entity_id"] == "LOG001"
        assert "entity_info" in result
        assert "summary" in result
        assert "audit_trail" in result
        
        # Check summary
        summary = result["summary"]
        assert summary["total_events"] >= 3
        assert summary["access_attempts"] >= 3
        
        # Check audit events
        audit_events = result["audit_trail"]
        assert len(audit_events) >= 3
        for event in audit_events:
            assert "type" in event
            assert "timestamp" in event
            assert "summary" in event
        
        # Test vehicle audit trail
        result = logging_service.get_audit_trail("vehicle", "LOG123", days=7)
        assert result["success"] is True
        assert result["entity_type"] == "vehicle"
        
        db.close()
    
    def test_export_logs(self):
        """Test log export functionality"""
        db = TestingSessionLocal()
        logging_service = LoggingService(db)
        
        # Create test logs for export
        for i in range(3):
            logging_service.log_access_attempt(
                gate_id="EXPORT_GATE",
                user_id="LOG001",
                access_granted=True,
                notes=f"Export test {i}"
            )
        
        # Test JSON export
        result = logging_service.export_logs({}, "json")
        assert result["success"] is True
        assert result["format"] == "json"
        assert "data" in result
        assert "filename" in result
        
        # Test CSV export
        result = logging_service.export_logs({}, "csv")
        assert result["success"] is True
        assert result["format"] == "csv"
        assert isinstance(result["data"], str)
        assert "timestamp,gate_id" in result["data"]  # Check CSV header
        
        # Test invalid format
        result = logging_service.export_logs({}, "xml")
        assert result["success"] is False
        assert "Unsupported export format" in result["error"]
        
        db.close()
    
    def test_cleanup_old_logs(self):
        """Test cleanup of old logs"""
        db = TestingSessionLocal()
        logging_service = LoggingService(db)
        
        # Create old logs (simulate by creating logs and then manually updating timestamps)
        old_logs = []
        for i in range(3):
            result = logging_service.log_access_attempt(
                gate_id="CLEANUP_GATE",
                user_id="LOG001",
                access_granted=True,
                notes=f"Old log {i}"
            )
            old_logs.append(result["log_id"])
        
        # Manually update timestamps to make them old
        old_date = datetime.now() - timedelta(days=100)
        for log_id in old_logs:
            log = db.query(AccessLog).filter(AccessLog.id == log_id).first()
            if log:
                log.timestamp = old_date
        db.commit()
        
        # Test cleanup
        result = logging_service.cleanup_old_logs(days_to_keep=30)
        assert result["success"] is True
        assert result["deleted_logs"] >= 3
        assert "cleanup_timestamp" in result
        
        db.close()

class TestLogsAPI:
    """Test suite for logs API endpoints"""
    
    @classmethod
    def setup_class(cls):
        """Set up test client"""
        cls.client = TestClient(app)
    
    def test_get_logs_endpoint(self):
        """Test GET /api/logs/ endpoint"""
        response = self.client.get("/api/logs/?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["logs"], list)
    
    def test_create_log_endpoint(self):
        """Test POST /api/logs/ endpoint"""
        response = self.client.post(
            "/api/logs/?gate_id=API_TEST&user_id=LOG001&access_granted=true&notes=API test log"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "log_id" in data
        assert "timestamp" in data
    
    def test_get_statistics_endpoint(self):
        """Test GET /api/logs/statistics endpoint"""
        response = self.client.get("/api/logs/statistics?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "basic_statistics" in data
        assert "security_metrics" in data
    
    def test_get_audit_trail_endpoint(self):
        """Test GET /api/logs/audit/{entity_type}/{entity_id} endpoint"""
        response = self.client.get("/api/logs/audit/user/LOG001?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["entity_type"] == "user"
        assert data["entity_id"] == "LOG001"
        assert "audit_trail" in data
    
    def test_export_logs_endpoint(self):
        """Test GET /api/logs/export endpoint"""
        # Test JSON export
        response = self.client.get("/api/logs/export?format_type=json")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Test CSV export
        response = self.client.get("/api/logs/export?format_type=csv")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    def test_get_recent_logs_endpoint(self):
        """Test GET /api/logs/recent endpoint"""
        response = self.client.get("/api/logs/recent?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "timestamp" in data
        assert len(data["logs"]) <= 5
    
    def test_get_denied_logs_endpoint(self):
        """Test GET /api/logs/denied endpoint"""
        response = self.client.get("/api/logs/denied?limit=10&days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "days" in data
        # All returned logs should have access_granted = false
        for log in data["logs"]:
            assert log["access_granted"] is False
    
    def test_search_logs_endpoint(self):
        """Test GET /api/logs/search endpoint"""
        response = self.client.get("/api/logs/search?q=LOG001&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "search_term" in data
        assert data["search_term"] == "LOG001"
    
    def test_get_log_by_id_endpoint(self):
        """Test GET /api/logs/{log_id} endpoint"""
        # First create a log to get its ID
        create_response = self.client.post(
            "/api/logs/?gate_id=ID_TEST&user_id=LOG001&access_granted=true"
        )
        
        assert create_response.status_code == 200
        log_id = create_response.json()["log_id"]
        
        # Now get the log by ID
        response = self.client.get(f"/api/logs/{log_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "log" in data
        assert data["log"]["id"] == log_id
    
    def test_cleanup_endpoint(self):
        """Test DELETE /api/logs/cleanup endpoint"""
        # Test without confirmation (should fail)
        response = self.client.delete("/api/logs/cleanup?days_to_keep=30")
        
        assert response.status_code == 400
        assert "confirmation" in response.json()["detail"]
        
        # Test with confirmation
        response = self.client.delete("/api/logs/cleanup?days_to_keep=30&confirm=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "deleted_logs" in data
        assert "deleted_alerts" in data

def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v"])

if __name__ == "__main__":
    run_tests()