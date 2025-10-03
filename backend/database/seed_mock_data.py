#!/usr/bin/env python3
"""
Mock data seeding for Smart Campus Access Control
Creates realistic test data for demonstration and development
"""

import sys
import os
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_session, create_tables
from models import User, Vehicle, AccessLog, Alert, UserRole, UserStatus, VehicleType, VehicleStatus, VerificationMethod, AlertType
from services.database_service import DatabaseService

class MockDataSeeder:
    """
    Comprehensive mock data seeder for the Smart Campus Access Control system
    """
    
    def __init__(self):
        self.users_data = []
        self.vehicles_data = []
        self.access_logs_data = []
        self.alerts_data = []
    
    def generate_users(self) -> List[Dict[str, Any]]:
        """Generate realistic user data"""
        users = [
            # Students
            {
                "id": "STU001",
                "name": "John Doe",
                "email": "john.doe@university.edu",
                "role": UserRole.STUDENT,
                "department": "Computer Science",
                "status": UserStatus.ACTIVE
            },
            {
                "id": "STU002", 
                "name": "Alice Johnson",
                "email": "alice.johnson@university.edu",
                "role": UserRole.STUDENT,
                "department": "Engineering",
                "status": UserStatus.ACTIVE
            },
            {
                "id": "STU003",
                "name": "Bob Wilson",
                "email": "bob.wilson@university.edu", 
                "role": UserRole.STUDENT,
                "department": "Mathematics",
                "status": UserStatus.ACTIVE
            },
            {
                "id": "STU004",
                "name": "Emma Davis",
                "email": "emma.davis@university.edu",
                "role": UserRole.STUDENT,
                "department": "Physics",
                "status": UserStatus.ACTIVE
            },
            {
                "id": "STU005",
                "name": "Michael Chen",
                "email": "michael.chen@university.edu",
                "role": UserRole.STUDENT,
                "department": "Computer Science", 
                "status": UserStatus.INACTIVE  # Inactive student for testing
            },
            
            # Staff
            {
                "id": "STF001",
                "name": "Jane Smith",
                "email": "jane.smith@university.edu",
                "role": UserRole.STAFF,
                "department": "Administration",
                "status": UserStatus.ACTIVE
            },
            {
                "id": "STF002",
                "name": "Michael Brown",
                "email": "michael.brown@university.edu",
                "role": UserRole.STAFF,
                "department": "Security",
                "status": UserStatus.ACTIVE
            },
            {
                "id": "STF003",
                "name": "Sarah Miller",
                "email": "sarah.miller@university.edu",
                "role": UserRole.STAFF,
                "department": "IT Services",
                "status": UserStatus.ACTIVE
            },
            
            # Faculty
            {
                "id": "FAC001",
                "name": "Dr. Robert Taylor",
                "email": "robert.taylor@university.edu",
                "role": UserRole.FACULTY,
                "department": "Computer Science",
                "status": UserStatus.ACTIVE
            },
            {
                "id": "FAC002",
                "name": "Prof. Lisa Anderson",
                "email": "lisa.anderson@university.edu",
                "role": UserRole.FACULTY,
                "department": "Engineering",
                "status": UserStatus.ACTIVE
            }
        ]
        
        self.users_data = users
        return users
    
    def generate_vehicles(self) -> List[Dict[str, Any]]:
        """Generate realistic vehicle data"""
        vehicles = [
            # Student vehicles
            {
                "license_plate": "ABC123",
                "owner_id": "STU001",
                "vehicle_type": VehicleType.CAR,
                "color": "Blue",
                "model": "Honda Civic",
                "status": VehicleStatus.ACTIVE
            },
            {
                "license_plate": "DEF456", 
                "owner_id": "STU002",
                "vehicle_type": VehicleType.MOTORCYCLE,
                "color": "Black",
                "model": "Yamaha R15",
                "status": VehicleStatus.ACTIVE
            },
            {
                "license_plate": "JKL012",
                "owner_id": "STU003",
                "vehicle_type": VehicleType.BICYCLE,
                "color": "Green",
                "model": "Trek Mountain",
                "status": VehicleStatus.ACTIVE
            },
            {
                "license_plate": "PQR678",
                "owner_id": "STU004",
                "vehicle_type": VehicleType.MOTORCYCLE,
                "color": "Red", 
                "model": "Honda CBR",
                "status": VehicleStatus.ACTIVE
            },
            {
                "license_plate": "STU999",
                "owner_id": "STU005",  # Inactive user
                "vehicle_type": VehicleType.CAR,
                "color": "White",
                "model": "Toyota Corolla",
                "status": VehicleStatus.INACTIVE  # Inactive vehicle for testing
            },
            
            # Staff vehicles
            {
                "license_plate": "XYZ789",
                "owner_id": "STF001",
                "vehicle_type": VehicleType.CAR,
                "color": "Red",
                "model": "Toyota Camry",
                "status": VehicleStatus.ACTIVE
            },
            {
                "license_plate": "MNO345",
                "owner_id": "STF002",
                "vehicle_type": VehicleType.CAR,
                "color": "Silver",
                "model": "Ford Focus",
                "status": VehicleStatus.ACTIVE
            },
            {
                "license_plate": "VWX234",
                "owner_id": "STF003",
                "vehicle_type": VehicleType.CAR,
                "color": "Blue",
                "model": "Nissan Altima",
                "status": VehicleStatus.ACTIVE
            },
            
            # Faculty vehicles
            {
                "license_plate": "GHI789",
                "owner_id": "FAC001",
                "vehicle_type": VehicleType.CAR,
                "color": "White",
                "model": "BMW 320i",
                "status": VehicleStatus.ACTIVE
            },
            {
                "license_plate": "YZA567",
                "owner_id": "FAC002",
                "vehicle_type": VehicleType.CAR,
                "color": "Gray",
                "model": "Mercedes C-Class",
                "status": VehicleStatus.ACTIVE
            }
        ]
        
        self.vehicles_data = vehicles
        return vehicles
    
    def generate_access_logs(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Generate realistic access log data for the past few days"""
        logs = []
        
        # Get user and vehicle IDs for realistic data
        user_ids = [user["id"] for user in self.users_data if user["status"] == UserStatus.ACTIVE]
        vehicle_plates = [vehicle["license_plate"] for vehicle in self.vehicles_data if vehicle["status"] == VehicleStatus.ACTIVE]
        
        # Generate logs for each day
        for day in range(days_back):
            date = datetime.now() - timedelta(days=day)
            
            # Generate 15-25 access attempts per day
            daily_attempts = random.randint(15, 25)
            
            for _ in range(daily_attempts):
                # Random time during the day (mostly business hours)
                if random.random() < 0.8:  # 80% during business hours
                    hour = random.randint(7, 18)
                else:  # 20% outside business hours
                    hour = random.choice([6, 19, 20, 21, 22])
                
                minute = random.randint(0, 59)
                timestamp = date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
                
                # Determine verification scenario
                scenario = random.choices(
                    ["both_valid", "id_only_valid", "vehicle_only_valid", "both_invalid", "id_invalid", "vehicle_invalid"],
                    weights=[40, 25, 20, 5, 5, 5]  # Most attempts are successful
                )[0]
                
                if scenario == "both_valid":
                    user_id = random.choice(user_ids)
                    # Find a vehicle owned by this user
                    user_vehicles = [v["license_plate"] for v in self.vehicles_data if v["owner_id"] == user_id and v["status"] == VehicleStatus.ACTIVE]
                    license_plate = random.choice(user_vehicles) if user_vehicles else random.choice(vehicle_plates)
                    verification_method = VerificationMethod.BOTH
                    access_granted = True
                    
                elif scenario == "id_only_valid":
                    user_id = random.choice(user_ids)
                    license_plate = None
                    verification_method = VerificationMethod.ID_ONLY
                    access_granted = True
                    
                elif scenario == "vehicle_only_valid":
                    user_id = None
                    license_plate = random.choice(vehicle_plates)
                    verification_method = VerificationMethod.VEHICLE_ONLY
                    access_granted = True
                    
                elif scenario == "both_invalid":
                    user_id = f"INVALID{random.randint(100, 999)}"
                    license_plate = f"FAKE{random.randint(100, 999)}"
                    verification_method = VerificationMethod.BOTH
                    access_granted = False
                    
                elif scenario == "id_invalid":
                    user_id = f"INVALID{random.randint(100, 999)}"
                    license_plate = None
                    verification_method = VerificationMethod.ID_ONLY
                    access_granted = False
                    
                else:  # vehicle_invalid
                    user_id = None
                    license_plate = f"FAKE{random.randint(100, 999)}"
                    verification_method = VerificationMethod.VEHICLE_ONLY
                    access_granted = False
                
                # Generate notes
                if access_granted:
                    notes = f"Successful {verification_method.value} verification"
                else:
                    notes = f"Failed {verification_method.value} verification - unauthorized attempt"
                
                log_entry = {
                    "timestamp": timestamp,
                    "gate_id": random.choice(["MAIN_GATE", "SIDE_GATE", "PARKING_GATE"]),
                    "user_id": user_id,
                    "license_plate": license_plate,
                    "verification_method": verification_method,
                    "access_granted": access_granted,
                    "alert_triggered": not access_granted,
                    "notes": notes
                }
                
                logs.append(log_entry)
        
        # Sort by timestamp
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        self.access_logs_data = logs
        return logs
    
    def generate_alerts(self) -> List[Dict[str, Any]]:
        """Generate alerts based on failed access attempts"""
        alerts = []
        
        # Generate alerts from failed access logs
        failed_logs = [log for log in self.access_logs_data if not log["access_granted"]]
        
        for log in failed_logs[:15]:  # Create alerts for first 15 failed attempts
            if log["user_id"] and log["license_plate"]:
                alert_type = AlertType.UNAUTHORIZED_ID  # Prioritize ID alerts
                message = f"Unauthorized access attempt - ID: {log['user_id']}, Vehicle: {log['license_plate']}"
                user_id = log["user_id"]
                license_plate = log["license_plate"]
            elif log["user_id"]:
                alert_type = AlertType.UNAUTHORIZED_ID
                message = f"Unauthorized ID scan attempt - ID: {log['user_id']}"
                user_id = log["user_id"]
                license_plate = None
            else:
                alert_type = AlertType.UNAUTHORIZED_VEHICLE
                message = f"Unregistered vehicle detected - Plate: {log['license_plate']}"
                user_id = None
                license_plate = log["license_plate"]
            
            # Some alerts are resolved (70% chance)
            resolved = random.random() < 0.7
            resolved_at = log["timestamp"] + timedelta(hours=random.randint(1, 24)) if resolved else None
            
            alert = {
                "alert_type": alert_type,
                "message": message,
                "user_id": user_id,
                "license_plate": license_plate,
                "gate_id": log["gate_id"],
                "resolved": resolved,
                "created_at": log["timestamp"],
                "resolved_at": resolved_at
            }
            
            alerts.append(alert)
        
        # Add a few system error alerts
        for i in range(3):
            alert = {
                "alert_type": AlertType.SYSTEM_ERROR,
                "message": f"System error: Camera malfunction at gate {random.choice(['MAIN_GATE', 'SIDE_GATE'])}",
                "user_id": None,
                "license_plate": None,
                "gate_id": random.choice(["MAIN_GATE", "SIDE_GATE"]),
                "resolved": i < 2,  # First 2 are resolved
                "created_at": datetime.now() - timedelta(hours=random.randint(1, 48)),
                "resolved_at": datetime.now() - timedelta(hours=random.randint(1, 24)) if i < 2 else None
            }
            alerts.append(alert)
        
        self.alerts_data = alerts
        return alerts
    
    def seed_database(self, clear_existing: bool = True) -> Dict[str, Any]:
        """Seed the database with all mock data"""
        
        print("🌱 Starting mock data seeding...")
        
        try:
            with get_db_session() as db:
                db_service = DatabaseService(db)
                
                if clear_existing:
                    print("🧹 Clearing existing data...")
                    # Clear in reverse dependency order
                    db.query(Alert).delete()
                    db.query(AccessLog).delete()
                    db.query(Vehicle).delete()
                    db.query(User).delete()
                    db.commit()
                
                # Generate all data
                print("📊 Generating mock data...")
                users = self.generate_users()
                vehicles = self.generate_vehicles()
                access_logs = self.generate_access_logs(days_back=14)  # 2 weeks of data
                alerts = self.generate_alerts()
                
                # Seed users
                print("👥 Seeding users...")
                user_objects = []
                for user_data in users:
                    user = User(
                        id=user_data["id"],
                        name=user_data["name"],
                        email=user_data["email"],
                        role=user_data["role"],
                        department=user_data["department"],
                        status=user_data["status"]
                    )
                    db.add(user)
                    user_objects.append(user)
                
                db.commit()
                print(f"✅ Created {len(user_objects)} users")
                
                # Seed vehicles
                print("🚗 Seeding vehicles...")
                vehicle_objects = []
                for vehicle_data in vehicles:
                    vehicle = Vehicle(
                        license_plate=vehicle_data["license_plate"],
                        owner_id=vehicle_data["owner_id"],
                        vehicle_type=vehicle_data["vehicle_type"],
                        color=vehicle_data["color"],
                        model=vehicle_data["model"],
                        status=vehicle_data["status"]
                    )
                    db.add(vehicle)
                    vehicle_objects.append(vehicle)
                
                db.commit()
                print(f"✅ Created {len(vehicle_objects)} vehicles")
                
                # Seed access logs
                print("📋 Seeding access logs...")
                log_objects = []
                for log_data in access_logs:
                    access_log = AccessLog(
                        timestamp=log_data["timestamp"],
                        gate_id=log_data["gate_id"],
                        user_id=log_data["user_id"],
                        license_plate=log_data["license_plate"],
                        verification_method=log_data["verification_method"],
                        access_granted=log_data["access_granted"],
                        alert_triggered=log_data["alert_triggered"],
                        notes=log_data["notes"]
                    )
                    db.add(access_log)
                    log_objects.append(access_log)
                
                db.commit()
                print(f"✅ Created {len(log_objects)} access logs")
                
                # Seed alerts
                print("🚨 Seeding alerts...")
                alert_objects = []
                for alert_data in alerts:
                    alert = Alert(
                        alert_type=alert_data["alert_type"],
                        message=alert_data["message"],
                        user_id=alert_data["user_id"],
                        license_plate=alert_data["license_plate"],
                        gate_id=alert_data["gate_id"],
                        resolved=alert_data["resolved"],
                        created_at=alert_data["created_at"],
                        resolved_at=alert_data["resolved_at"]
                    )
                    db.add(alert)
                    alert_objects.append(alert)
                
                db.commit()
                print(f"✅ Created {len(alert_objects)} alerts")
                
                # Generate summary statistics
                stats = db_service.get_dashboard_data(days=7)
                
                result = {
                    "success": True,
                    "message": "Mock data seeded successfully",
                    "counts": {
                        "users": len(user_objects),
                        "vehicles": len(vehicle_objects),
                        "access_logs": len(log_objects),
                        "alerts": len(alert_objects)
                    },
                    "statistics": stats
                }
                
                print("🎉 Mock data seeding completed successfully!")
                print(f"📊 Summary: {result['counts']}")
                
                return result
                
        except Exception as e:
            print(f"❌ Error seeding mock data: {e}")
            return {
                "success": False,
                "message": f"Error seeding mock data: {str(e)}",
                "counts": {},
                "statistics": {}
            }
    
    def create_demo_scenarios(self) -> Dict[str, Any]:
        """Create specific demo scenarios for presentation"""
        
        print("🎭 Creating demo scenarios...")
        
        try:
            with get_db_session() as db:
                # Demo scenario 1: Successful dual verification
                demo_log1 = AccessLog(
                    timestamp=datetime.now() - timedelta(minutes=5),
                    gate_id="MAIN_GATE",
                    user_id="STU001",
                    license_plate="ABC123",
                    verification_method=VerificationMethod.BOTH,
                    access_granted=True,
                    alert_triggered=False,
                    notes="DEMO: Successful dual verification - John Doe with Honda Civic"
                )
                db.add(demo_log1)
                
                # Demo scenario 2: Failed ID verification
                demo_log2 = AccessLog(
                    timestamp=datetime.now() - timedelta(minutes=3),
                    gate_id="MAIN_GATE", 
                    user_id="DEMO999",
                    license_plate=None,
                    verification_method=VerificationMethod.ID_ONLY,
                    access_granted=False,
                    alert_triggered=True,
                    notes="DEMO: Failed ID verification - Unknown student ID"
                )
                db.add(demo_log2)
                
                # Demo scenario 3: Unauthorized vehicle
                demo_log3 = AccessLog(
                    timestamp=datetime.now() - timedelta(minutes=1),
                    gate_id="PARKING_GATE",
                    user_id=None,
                    license_plate="DEMO123",
                    verification_method=VerificationMethod.VEHICLE_ONLY,
                    access_granted=False,
                    alert_triggered=True,
                    notes="DEMO: Unregistered vehicle detected"
                )
                db.add(demo_log3)
                
                # Create corresponding alerts
                demo_alert1 = Alert(
                    alert_type=AlertType.UNAUTHORIZED_ID,
                    message="DEMO: Unauthorized ID scan attempt - ID: DEMO999",
                    user_id="DEMO999",
                    license_plate=None,
                    gate_id="MAIN_GATE",
                    resolved=False,
                    created_at=datetime.now() - timedelta(minutes=3)
                )
                db.add(demo_alert1)
                
                demo_alert2 = Alert(
                    alert_type=AlertType.UNAUTHORIZED_VEHICLE,
                    message="DEMO: Unregistered vehicle detected - Plate: DEMO123",
                    user_id=None,
                    license_plate="DEMO123",
                    gate_id="PARKING_GATE",
                    resolved=False,
                    created_at=datetime.now() - timedelta(minutes=1)
                )
                db.add(demo_alert2)
                
                db.commit()
                
                print("✅ Demo scenarios created successfully")
                return {
                    "success": True,
                    "message": "Demo scenarios created",
                    "scenarios": [
                        "Successful dual verification (STU001 + ABC123)",
                        "Failed ID verification (DEMO999)",
                        "Unauthorized vehicle (DEMO123)"
                    ]
                }
                
        except Exception as e:
            print(f"❌ Error creating demo scenarios: {e}")
            return {
                "success": False,
                "message": f"Error creating demo scenarios: {str(e)}"
            }

def main():
    """Main function to run the seeder"""
    print("🏫 Smart Campus Access Control - Mock Data Seeder")
    print("=" * 50)
    
    # Ensure tables exist
    create_tables()
    
    # Create seeder instance
    seeder = MockDataSeeder()
    
    # Seed database
    result = seeder.seed_database(clear_existing=True)
    
    if result["success"]:
        # Create demo scenarios
        demo_result = seeder.create_demo_scenarios()
        
        print("\n📋 Seeding Summary:")
        print(f"Users: {result['counts']['users']}")
        print(f"Vehicles: {result['counts']['vehicles']}")
        print(f"Access Logs: {result['counts']['access_logs']}")
        print(f"Alerts: {result['counts']['alerts']}")
        
        if demo_result["success"]:
            print(f"Demo Scenarios: {len(demo_result['scenarios'])}")
        
        print("\n🎯 Ready for demonstration!")
        print("💡 Use the management utility to explore the data:")
        print("   python database/manage_db.py status")
        print("   python database/manage_db.py logs")
        print("   python database/manage_db.py alerts")
        
    else:
        print(f"\n❌ Seeding failed: {result['message']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())