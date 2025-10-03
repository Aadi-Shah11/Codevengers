#!/usr/bin/env python3
"""
SQLite database initialization script for Smart Campus Access Control
Creates database, tables, and populates with mock data using SQLAlchemy
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from config import settings
from models.user import User
from models.vehicle import Vehicle, VehicleType, VehicleStatus
from models.access_log import AccessLog, AccessResult
from models.alert import Alert, AlertType, AlertSeverity
from database.connection import Base
import datetime

def create_database():
    """Create SQLite database and tables"""
    try:
        print("🚀 Initializing Smart Campus Access Control Database (SQLite)...")
        
        # Create engine
        engine = create_engine(settings.DATABASE_URL, echo=False)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        return engine
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return None

def seed_data(engine):
    """Populate database with sample data"""
    try:
        print("🌱 Inserting seed data...")
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Sample users
        users = [
            User(
                user_id="USER001",
                name="John Doe",
                email="john.doe@campus.edu",
                phone="555-0101",
                role="student",
                status="active",
                created_at=datetime.datetime.now()
            ),
            User(
                user_id="USER002", 
                name="Jane Smith",
                email="jane.smith@campus.edu",
                phone="555-0102",
                role="faculty",
                status="active",
                created_at=datetime.datetime.now()
            ),
            User(
                user_id="USER003",
                name="Bob Johnson", 
                email="bob.johnson@campus.edu",
                phone="555-0103",
                role="staff",
                status="active",
                created_at=datetime.datetime.now()
            ),
            User(
                user_id="USER004",
                name="Alice Brown",
                email="alice.brown@campus.edu", 
                phone="555-0104",
                role="student",
                status="active",
                created_at=datetime.datetime.now()
            ),
            User(
                user_id="USER005",
                name="Charlie Wilson",
                email="charlie.wilson@campus.edu",
                phone="555-0105", 
                role="visitor",
                status="active",
                created_at=datetime.datetime.now()
            )
        ]
        
        # Add users
        for user in users:
            db.add(user)
        
        # Sample vehicles
        vehicles = [
            Vehicle(
                license_plate="ABC123",
                owner_id="USER001",
                vehicle_type=VehicleType.CAR,
                color="blue",
                model="Honda Civic",
                status=VehicleStatus.ACTIVE,
                created_at=datetime.datetime.now()
            ),
            Vehicle(
                license_plate="XYZ789",
                owner_id="USER002", 
                vehicle_type=VehicleType.CAR,
                color="red",
                model="Toyota Camry",
                status=VehicleStatus.ACTIVE,
                created_at=datetime.datetime.now()
            ),
            Vehicle(
                license_plate="DEF456",
                owner_id="USER003",
                vehicle_type=VehicleType.MOTORCYCLE,
                color="black",
                model="Yamaha R1",
                status=VehicleStatus.ACTIVE,
                created_at=datetime.datetime.now()
            ),
            Vehicle(
                license_plate="GHI789",
                owner_id="USER004",
                vehicle_type=VehicleType.CAR,
                color="white",
                model="Ford Focus",
                status=VehicleStatus.ACTIVE,
                created_at=datetime.datetime.now()
            ),
            Vehicle(
                license_plate="JKL012",
                owner_id="USER005",
                vehicle_type=VehicleType.BICYCLE,
                color="green",
                model="Trek Mountain Bike",
                status=VehicleStatus.ACTIVE,
                created_at=datetime.datetime.now()
            )
        ]
        
        # Add vehicles
        for vehicle in vehicles:
            db.add(vehicle)
        
        # Sample access logs
        access_logs = [
            AccessLog(
                user_id="USER001",
                license_plate="ABC123",
                gate_id="MAIN_GATE",
                access_result=AccessResult.GRANTED,
                verification_method="id_scan",
                timestamp=datetime.datetime.now() - datetime.timedelta(hours=2)
            ),
            AccessLog(
                user_id="USER002",
                license_plate="XYZ789", 
                gate_id="PARKING_A",
                access_result=AccessResult.GRANTED,
                verification_method="vehicle_ocr",
                timestamp=datetime.datetime.now() - datetime.timedelta(hours=1)
            ),
            AccessLog(
                user_id=None,
                license_plate="UNKNOWN",
                gate_id="MAIN_GATE",
                access_result=AccessResult.DENIED,
                verification_method="vehicle_ocr",
                timestamp=datetime.datetime.now() - datetime.timedelta(minutes=30)
            )
        ]
        
        # Add access logs
        for log in access_logs:
            db.add(log)
        
        # Sample alerts
        alerts = [
            Alert(
                alert_type=AlertType.UNAUTHORIZED_ACCESS,
                severity=AlertSeverity.HIGH,
                message="Unauthorized vehicle detected: UNKNOWN",
                gate_id="MAIN_GATE",
                user_id=None,
                license_plate="UNKNOWN",
                timestamp=datetime.datetime.now() - datetime.timedelta(minutes=30),
                resolved=False
            )
        ]
        
        # Add alerts
        for alert in alerts:
            db.add(alert)
        
        # Commit all changes
        db.commit()
        
        # Verify data
        user_count = db.query(User).count()
        vehicle_count = db.query(Vehicle).count()
        log_count = db.query(AccessLog).count()
        alert_count = db.query(Alert).count()
        
        print(f"✅ Seed data inserted successfully:")
        print(f"  - Users: {user_count}")
        print(f"  - Vehicles: {vehicle_count}")
        print(f"  - Access Logs: {log_count}")
        print(f"  - Alerts: {alert_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inserting seed data: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def verify_database(engine):
    """Verify database setup"""
    try:
        print("🔍 Verifying database setup...")
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Test queries
        users = db.query(User).all()
        vehicles = db.query(Vehicle).all()
        
        print(f"✅ Database verification successful:")
        print(f"  - Found {len(users)} users")
        print(f"  - Found {len(vehicles)} vehicles")
        
        # Show sample data
        if users:
            print(f"  - Sample user: {users[0].name} ({users[0].user_id})")
        if vehicles:
            print(f"  - Sample vehicle: {vehicles[0].license_plate} ({vehicles[0].model})")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main initialization function"""
    try:
        # Create database and tables
        engine = create_database()
        if not engine:
            sys.exit(1)
        
        # Insert seed data
        if not seed_data(engine):
            sys.exit(1)
        
        # Verify setup
        if not verify_database(engine):
            sys.exit(1)
        
        print("\n🎉 Database initialization completed successfully!")
        print(f"📁 Database file: {settings.DATABASE_URL.replace('sqlite:///', '')}")
        print("\n📝 Next steps:")
        print("  1. Start the FastAPI backend: uvicorn main:app --reload")
        print("  2. Open API docs: http://localhost:8000/docs")
        print("  3. Test vehicle registration and OCR")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()