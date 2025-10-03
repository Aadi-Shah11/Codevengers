#!/usr/bin/env python3
"""
Vehicle Registration Demo Script
Demonstrates the vehicle registration and management functionality
"""

import requests
import json
import time
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class VehicleRegistrationDemo:
    """
    Demonstration of vehicle registration functionality
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_api_connection(self):
        """Test if API is accessible"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ API connection successful")
                return True
            else:
                print(f"❌ API connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API connection error: {e}")
            return False
    
    def register_vehicle(self, license_plate: str, owner_id: str, vehicle_type: str, 
                        color: str = None, model: str = None):
        """Register a vehicle"""
        try:
            data = {
                "license_plate": license_plate,
                "owner_id": owner_id,
                "vehicle_type": vehicle_type
            }
            
            if color:
                data["color"] = color
            if model:
                data["model"] = model
            
            response = self.session.post(
                f"{self.base_url}/api/vehicles/register",
                json=data
            )
            
            return response.json(), response.status_code
            
        except Exception as e:
            return {"error": str(e)}, 500
    
    def demonstrate_successful_registration(self):
        """Demonstrate successful vehicle registrations"""
        print("\n🚗 Testing Successful Vehicle Registration")
        print("-" * 50)
        
        test_cases = [
            {
                "plate": "DEMO001",
                "owner": "STU001",
                "type": "car",
                "color": "Blue",
                "model": "Honda Civic",
                "description": "Student Car Registration"
            },
            {
                "plate": "DEMO002",
                "owner": "STF001",
                "type": "motorcycle",
                "color": "Black",
                "model": "Yamaha R15",
                "description": "Staff Motorcycle Registration"
            },
            {
                "plate": "DEMO003",
                "owner": "FAC001",
                "type": "bicycle",
                "color": "Green",
                "model": "Trek Mountain",
                "description": "Faculty Bicycle Registration"
            }
        ]
        
        for case in test_cases:
            print(f"\n📋 {case['description']}")
            result, status_code = self.register_vehicle(
                case["plate"], case["owner"], case["type"], 
                case["color"], case["model"]
            )
            
            if status_code == 200 and result.get("success"):
                print(f"✅ Registration SUCCESSFUL")
                print(f"   License Plate: {result['vehicle']['license_plate']}")
                print(f"   Owner: {result['vehicle']['owner_name']} ({result['vehicle']['owner_id']})")
                print(f"   Vehicle: {result['vehicle']['color']} {result['vehicle']['model']} ({result['vehicle']['vehicle_type']})")
                print(f"   Registration Time: {result.get('registration_timestamp', 'N/A')}")
            else:
                print(f"❌ Registration FAILED")
                print(f"   Error: {result.get('message', result.get('error', 'Unknown error'))}")
    
    def demonstrate_registration_failures(self):
        """Demonstrate various registration failure scenarios"""
        print("\n🚫 Testing Registration Failure Scenarios")
        print("-" * 50)
        
        test_cases = [
            {
                "plate": "DEMO001",  # Duplicate plate
                "owner": "STU002",
                "type": "car",
                "description": "Duplicate License Plate"
            },
            {
                "plate": "INVALID",
                "owner": "NONEXISTENT999",
                "type": "car",
                "description": "Non-existent Owner"
            },
            {
                "plate": "INACTIVE",
                "owner": "STU005",  # Inactive user
                "type": "car",
                "description": "Inactive Owner Account"
            },
            {
                "plate": "BADTYPE",
                "owner": "STU001",
                "type": "airplane",  # Invalid vehicle type
                "description": "Invalid Vehicle Type"
            },
            {
                "plate": "AB",  # Too short
                "owner": "STU001",
                "type": "car",
                "description": "Invalid License Plate Format"
            }
        ]
        
        for case in test_cases:
            print(f"\n📋 {case['description']}")
            result, status_code = self.register_vehicle(
                case["plate"], case["owner"], case["type"]
            )
            
            print(f"❌ Registration FAILED (Expected)")
            if "detail" in result:
                print(f"   Error: {result['detail'].get('error', result['detail'])}")
                if isinstance(result['detail'], dict) and 'error_code' in result['detail']:
                    print(f"   Error Code: {result['detail']['error_code']}")
            else:
                print(f"   Error: {result.get('message', result.get('error', 'Unknown error'))}")
    
    def demonstrate_vehicle_management(self):
        """Demonstrate vehicle management operations"""
        print("\n🔧 Testing Vehicle Management Operations")
        print("-" * 50)
        
        # Register a vehicle for management testing
        print("\n📋 Registering Vehicle for Management Testing")
        result, status_code = self.register_vehicle("MGMT001", "STF001", "car", "Silver", "Toyota Camry")
        
        if status_code == 200:
            print("✅ Management test vehicle registered")
            
            # Test vehicle information retrieval
            print("\n📋 Getting Vehicle Information")
            try:
                response = self.session.get(f"{self.base_url}/api/vehicles/MGMT001")
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Vehicle info retrieved successfully")
                    print(f"   License Plate: {data['vehicle']['license_plate']}")
                    print(f"   Owner: {data['vehicle']['owner_name']}")
                    print(f"   Type: {data['vehicle']['vehicle_type']}")
                else:
                    print(f"❌ Failed to get vehicle info: {response.status_code}")
            except Exception as e:
                print(f"❌ Error getting vehicle info: {e}")
            
            # Test vehicle update
            print("\n📋 Updating Vehicle Information")
            try:
                response = self.session.put(
                    f"{self.base_url}/api/vehicles/MGMT001",
                    json={
                        "color": "Red",
                        "model": "Toyota Camry Hybrid"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Vehicle updated successfully")
                    print(f"   New Color: {data['vehicle']['color']}")
                    print(f"   New Model: {data['vehicle']['model']}")
                else:
                    print(f"❌ Failed to update vehicle: {response.status_code}")
            except Exception as e:
                print(f"❌ Error updating vehicle: {e}")
            
            # Test ownership transfer
            print("\n📋 Testing Ownership Transfer")
            try:
                response = self.session.post(
                    f"{self.base_url}/api/vehicles/MGMT001/transfer",
                    json={
                        "new_owner_id": "FAC001"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Ownership transferred successfully")
                    print(f"   New Owner: {data['new_owner']['owner_name']} ({data['new_owner']['owner_id']})")
                else:
                    print(f"❌ Failed to transfer ownership: {response.status_code}")
            except Exception as e:
                print(f"❌ Error transferring ownership: {e}")
        else:
            print("❌ Failed to register management test vehicle")
    
    def demonstrate_vehicle_verification(self):
        """Demonstrate vehicle verification"""
        print("\n🔍 Testing Vehicle Verification")
        print("-" * 50)
        
        # Test verification of registered vehicle
        print("\n📋 Verifying Registered Vehicle")
        try:
            response = self.session.post(f"{self.base_url}/api/vehicles/verify/ABC123")
            
            if response.status_code == 200:
                data = response.json()
                if data["access_granted"]:
                    print("✅ Vehicle AUTHORIZED")
                    print(f"   License Plate: {data['license_plate']}")
                    print(f"   Owner: {data['owner_name']}")
                    print(f"   Vehicle Type: {data['vehicle_type']}")
                    print(f"   Security Level: {data['security_level']}")
                else:
                    print("❌ Vehicle UNAUTHORIZED")
                    print(f"   Reason: {data['decision_reason']}")
            else:
                print(f"❌ Verification failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error verifying vehicle: {e}")
        
        # Test verification of unregistered vehicle
        print("\n📋 Verifying Unregistered Vehicle")
        try:
            response = self.session.post(f"{self.base_url}/api/vehicles/verify/UNREGISTERED999")
            
            if response.status_code == 200:
                data = response.json()
                print("❌ Vehicle UNAUTHORIZED (Expected)")
                print(f"   Reason: {data['decision_reason']}")
                if data.get("alert_ids"):
                    print(f"   🚨 Security Alert Generated: {data['alert_ids']}")
            else:
                print(f"❌ Verification failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error verifying vehicle: {e}")
    
    def demonstrate_video_upload(self):
        """Demonstrate video upload simulation"""
        print("\n📹 Testing Video Upload (Simulation)")
        print("-" * 50)
        
        # Create a dummy video file for testing
        print("\n📋 Simulating Video Upload")
        try:
            # Create a small dummy file to simulate video upload
            dummy_content = b"This is a dummy video file for testing purposes"
            
            files = {
                'video_file': ('test_video.mp4', dummy_content, 'video/mp4')
            }
            
            response = self.session.post(
                f"{self.base_url}/api/vehicles/upload_video?gate_id=MAIN_GATE",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Video processed successfully")
                print(f"   Filename: {data['filename']}")
                print(f"   File Size: {data['file_size']} bytes")
                print(f"   Processing Time: {data['processing_time']}s")
                print(f"   Detected Plate: {data['ocr_results']['license_plate']}")
                print(f"   OCR Confidence: {data['ocr_results']['confidence']}")
                print(f"   Access Decision: {'GRANTED' if data['verification']['access_granted'] else 'DENIED'}")
                print(f"   Note: {data['note']}")
            else:
                print(f"❌ Video upload failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error uploading video: {e}")
    
    def demonstrate_vehicle_listing(self):
        """Demonstrate vehicle listing and filtering"""
        print("\n📋 Testing Vehicle Listing and Filtering")
        print("-" * 50)
        
        # List all vehicles
        print("\n📋 Listing All Vehicles")
        try:
            response = self.session.get(f"{self.base_url}/api/vehicles/?limit=10")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['total']} vehicles")
                for vehicle in data['vehicles'][:3]:  # Show first 3
                    print(f"   - {vehicle['license_plate']}: {vehicle['vehicle_type']} owned by {vehicle['owner_name']}")
            else:
                print(f"❌ Failed to list vehicles: {response.status_code}")
        except Exception as e:
            print(f"❌ Error listing vehicles: {e}")
        
        # List vehicles by owner
        print("\n📋 Listing Vehicles by Owner")
        try:
            response = self.session.get(f"{self.base_url}/api/vehicles/owner/STU001")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {data['total']} vehicles for owner STU001")
                for vehicle in data['vehicles']:
                    print(f"   - {vehicle['license_plate']}: {vehicle['vehicle_type']}")
            else:
                print(f"❌ Failed to list owner vehicles: {response.status_code}")
        except Exception as e:
            print(f"❌ Error listing owner vehicles: {e}")
    
    def get_registration_statistics(self):
        """Get and display registration statistics"""
        print("\n📊 Vehicle Registration Statistics")
        print("-" * 50)
        
        try:
            response = self.session.get(f"{self.base_url}/api/vehicles/statistics/registration")
            
            if response.status_code == 200:
                stats = response.json()
                
                overall = stats.get("overall_statistics", {})
                print(f"📈 Overall Statistics:")
                print(f"   Total Vehicles: {overall.get('total_vehicles', 0)}")
                print(f"   Active Vehicles: {overall.get('active_vehicles', 0)}")
                
                by_type = overall.get("by_type", {})
                print(f"\n🚗 By Vehicle Type:")
                for vehicle_type, count in by_type.items():
                    print(f"   {vehicle_type.title()}: {count}")
                
                limits = stats.get("limits_by_role", {})
                print(f"\n📏 Registration Limits by Role:")
                for role, limit in limits.items():
                    print(f"   {role.title()}: {limit} vehicles")
                
                recent = stats.get("recent_registrations", {})
                print(f"\n📅 Recent Activity:")
                print(f"   Last 30 Days: {recent.get('last_30_days', 0)} registrations")
                
            else:
                print(f"❌ Failed to get statistics: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
    
    def run_full_demo(self):
        """Run complete demonstration"""
        print("🏫 Smart Campus Access Control - Vehicle Registration Demo")
        print("=" * 70)
        
        # Test API connection
        if not self.test_api_connection():
            print("❌ Cannot connect to API. Make sure the server is running.")
            return
        
        # Run all demonstrations
        self.demonstrate_successful_registration()
        self.demonstrate_registration_failures()
        self.demonstrate_vehicle_management()
        self.demonstrate_vehicle_verification()
        self.demonstrate_video_upload()
        self.demonstrate_vehicle_listing()
        self.get_registration_statistics()
        
        print("\n" + "=" * 70)
        print("🎉 Vehicle Registration Demo Complete!")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vehicle Registration Demo")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--test", choices=["register", "manage", "verify", "upload", "list", "stats"], 
                       help="Run specific test")
    
    args = parser.parse_args()
    
    demo = VehicleRegistrationDemo(base_url=args.url)
    
    if args.test:
        if not demo.test_api_connection():
            return 1
            
        if args.test == "register":
            demo.demonstrate_successful_registration()
            demo.demonstrate_registration_failures()
        elif args.test == "manage":
            demo.demonstrate_vehicle_management()
        elif args.test == "verify":
            demo.demonstrate_vehicle_verification()
        elif args.test == "upload":
            demo.demonstrate_video_upload()
        elif args.test == "list":
            demo.demonstrate_vehicle_listing()
        elif args.test == "stats":
            demo.get_registration_statistics()
    else:
        demo.run_full_demo()
    
    return 0

if __name__ == "__main__":
    exit(main())