#!/usr/bin/env python3
"""
Logging Service Demo Script
Demonstrates comprehensive logging and audit trail functionality
"""

import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LoggingServiceDemo:
    """
    Demonstration of logging service functionality
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
    
    def create_sample_logs(self):
        """Create sample access logs for demonstration"""
        print("\n📝 Creating Sample Access Logs")
        print("-" * 40)
        
        sample_logs = [
            {
                "gate_id": "MAIN_GATE",
                "user_id": "STU001",
                "access_granted": True,
                "notes": "Successful student access"
            },
            {
                "gate_id": "MAIN_GATE",
                "license_plate": "ABC123",
                "access_granted": True,
                "notes": "Vehicle verification successful"
            },
            {
                "gate_id": "SIDE_GATE",
                "user_id": "INVALID999",
                "access_granted": False,
                "notes": "Invalid student ID attempted"
            },
            {
                "gate_id": "PARKING_GATE",
                "license_plate": "FAKE123",
                "access_granted": False,
                "notes": "Unregistered vehicle detected"
            },
            {
                "gate_id": "MAIN_GATE",
                "user_id": "STF001",
                "license_plate": "XYZ789",
                "access_granted": True,
                "notes": "Staff dual verification"
            }
        ]
        
        created_logs = []
        
        for i, log_data in enumerate(sample_logs):
            try:
                # Build query parameters
                params = {
                    "gate_id": log_data["gate_id"],
                    "access_granted": str(log_data["access_granted"]).lower(),
                    "notes": log_data["notes"]
                }
                
                if "user_id" in log_data:
                    params["user_id"] = log_data["user_id"]
                if "license_plate" in log_data:
                    params["license_plate"] = log_data["license_plate"]
                
                response = self.session.post(f"{self.base_url}/api/logs/", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    created_logs.append(result["log_id"])
                    status = "✅ GRANTED" if log_data["access_granted"] else "❌ DENIED"
                    print(f"   Log {i+1}: {status} - {log_data['notes']}")
                else:
                    print(f"   Log {i+1}: ❌ Failed to create - {response.status_code}")
                    
            except Exception as e:
                print(f"   Log {i+1}: ❌ Error - {e}")
        
        print(f"\n✅ Created {len(created_logs)} sample logs")
        return created_logs
    
    def demonstrate_log_retrieval(self):
        """Demonstrate various log retrieval methods"""
        print("\n📋 Testing Log Retrieval Methods")
        print("-" * 40)
        
        # Get recent logs
        print("\n📋 Recent Access Logs")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/recent?limit=5")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data['logs'])} recent logs")
                
                for log in data['logs'][:3]:  # Show first 3
                    status = "✅ GRANTED" if log['access_granted'] else "❌ DENIED"
                    timestamp = log['timestamp'][:19]  # Remove microseconds
                    print(f"   {timestamp}: {status} at {log['gate_id']}")
                    if log.get('user_id'):
                        print(f"      User: {log['user_name']} ({log['user_id']})")
                    if log.get('license_plate'):
                        print(f"      Vehicle: {log['license_plate']}")
            else:
                print(f"❌ Failed to get recent logs: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting recent logs: {e}")
        
        # Get denied access logs
        print("\n📋 Denied Access Logs")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/denied?limit=5&days=7")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved {len(data['logs'])} denied access logs")
                
                for log in data['logs'][:3]:
                    timestamp = log['timestamp'][:19]
                    print(f"   {timestamp}: ❌ DENIED at {log['gate_id']}")
                    print(f"      Reason: {log.get('notes', 'No details')}")
                    if log.get('security_assessment'):
                        risk_level = log['security_assessment']['risk_level']
                        print(f"      Risk Level: {risk_level}")
            else:
                print(f"❌ Failed to get denied logs: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting denied logs: {e}")
        
        # Search logs
        print("\n📋 Search Functionality")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/search?q=STU001&limit=5")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found {len(data['logs'])} logs matching 'STU001'")
                
                for log in data['logs'][:2]:
                    status = "✅ GRANTED" if log['access_granted'] else "❌ DENIED"
                    print(f"   {log['timestamp'][:19]}: {status} - {log['user_id']}")
            else:
                print(f"❌ Failed to search logs: {response.status_code}")
        except Exception as e:
            print(f"❌ Error searching logs: {e}")
    
    def demonstrate_statistics(self):
        """Demonstrate access statistics and analytics"""
        print("\n📊 Testing Access Statistics and Analytics")
        print("-" * 40)
        
        # Get basic statistics
        print("\n📋 Access Statistics (Last 7 Days)")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/statistics?days=7")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["success"]:
                    basic_stats = data["basic_statistics"]
                    print("✅ Statistics retrieved successfully")
                    print(f"   Total Attempts: {basic_stats['total_attempts']}")
                    print(f"   Access Granted: {basic_stats['granted_count']}")
                    print(f"   Access Denied: {basic_stats['denied_count']}")
                    print(f"   Success Rate: {basic_stats['success_rate']}%")
                    print(f"   Unique Users: {basic_stats['unique_users']}")
                    print(f"   Unique Vehicles: {basic_stats['unique_vehicles']}")
                    
                    # Show verification methods
                    if "verification_methods" in data:
                        methods = data["verification_methods"]
                        print(f"\n📱 Verification Methods:")
                        print(f"   ID Only: {methods.get('id_only', 0)}")
                        print(f"   Vehicle Only: {methods.get('vehicle_only', 0)}")
                        print(f"   Both: {methods.get('both', 0)}")
                    
                    # Show security metrics
                    if "security_metrics" in data:
                        security = data["security_metrics"]
                        print(f"\n🔒 Security Metrics:")
                        print(f"   Security Score: {security.get('security_score', 0)}/100")
                        print(f"   Threat Level: {security.get('threat_level', 'UNKNOWN')}")
                        print(f"   Failed Attempts: {security.get('failed_attempts', 0)}")
                        print(f"   Alerts Triggered: {security.get('alerts_triggered', 0)}")
                else:
                    print(f"❌ Statistics request failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Failed to get statistics: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
        
        # Get hourly patterns
        print("\n📋 Hourly Access Patterns")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/patterns/hourly?days=7")
            
            if response.status_code == 200:
                data = response.json()
                patterns = data.get("patterns", [])
                
                if patterns:
                    print("✅ Hourly patterns retrieved")
                    print("   Peak hours (top 3):")
                    
                    # Sort by total attempts and show top 3
                    sorted_patterns = sorted(patterns, key=lambda x: x['total_attempts'], reverse=True)[:3]
                    for pattern in sorted_patterns:
                        hour = pattern['hour']
                        attempts = pattern['total_attempts']
                        success_rate = pattern['success_rate']
                        print(f"   {hour:02d}:00 - {attempts} attempts ({success_rate:.1f}% success)")
                else:
                    print("   No hourly patterns available")
            else:
                print(f"❌ Failed to get hourly patterns: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting hourly patterns: {e}")
    
    def demonstrate_audit_trail(self):
        """Demonstrate audit trail functionality"""
        print("\n🔍 Testing Audit Trail Functionality")
        print("-" * 40)
        
        # Get user audit trail
        print("\n📋 User Audit Trail (STU001)")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/audit/user/STU001?days=7")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["success"]:
                    print("✅ User audit trail retrieved")
                    
                    # Show entity info
                    if data.get("entity_info"):
                        entity = data["entity_info"]
                        print(f"   User: {entity['name']} ({entity['role']})")
                        print(f"   Department: {entity['department']}")
                    
                    # Show summary
                    summary = data["summary"]
                    print(f"\n📊 Activity Summary:")
                    print(f"   Total Events: {summary['total_events']}")
                    print(f"   Access Attempts: {summary['access_attempts']}")
                    print(f"   Successful Access: {summary['successful_access']}")
                    print(f"   Failed Access: {summary['failed_access']}")
                    print(f"   Security Alerts: {summary['security_alerts']}")
                    
                    # Show recent events
                    audit_trail = data["audit_trail"][:3]  # Show first 3 events
                    if audit_trail:
                        print(f"\n📋 Recent Activity:")
                        for event in audit_trail:
                            timestamp = event['timestamp'][:19]
                            event_type = event['type'].replace('_', ' ').title()
                            summary_text = event['summary']
                            print(f"   {timestamp}: {event_type} - {summary_text}")
                else:
                    print(f"❌ Audit trail request failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Failed to get user audit trail: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting user audit trail: {e}")
        
        # Get vehicle audit trail
        print("\n📋 Vehicle Audit Trail (ABC123)")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/audit/vehicle/ABC123?days=7")
            
            if response.status_code == 200:
                data = response.json()
                
                if data["success"]:
                    print("✅ Vehicle audit trail retrieved")
                    
                    # Show entity info
                    if data.get("entity_info"):
                        entity = data["entity_info"]
                        print(f"   Vehicle: {entity['license_plate']} ({entity['vehicle_type']})")
                        print(f"   Owner: {entity['owner_name']}")
                    
                    # Show summary
                    summary = data["summary"]
                    print(f"\n📊 Activity Summary:")
                    print(f"   Total Events: {summary['total_events']}")
                    print(f"   Access Attempts: {summary['access_attempts']}")
                    print(f"   Successful Access: {summary['successful_access']}")
                else:
                    print(f"❌ Vehicle audit trail request failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Failed to get vehicle audit trail: {response.status_code}")
        except Exception as e:
            print(f"❌ Error getting vehicle audit trail: {e}")
    
    def demonstrate_export_functionality(self):
        """Demonstrate log export functionality"""
        print("\n📤 Testing Log Export Functionality")
        print("-" * 40)
        
        # Test JSON export
        print("\n📋 JSON Export")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/export?format_type=json")
            
            if response.status_code == 200:
                print("✅ JSON export successful")
                print(f"   Content Type: {response.headers.get('content-type', 'N/A')}")
                print(f"   Content Length: {len(response.content)} bytes")
                
                # Try to parse JSON to verify format
                try:
                    data = response.json()
                    if isinstance(data, dict) and "export_timestamp" in str(data):
                        print("   ✅ Valid JSON format confirmed")
                    else:
                        print("   ⚠️ JSON format may be non-standard")
                except:
                    print("   ⚠️ Response is not valid JSON")
            else:
                print(f"❌ JSON export failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error with JSON export: {e}")
        
        # Test CSV export
        print("\n📋 CSV Export")
        try:
            response = self.session.get(f"{self.base_url}/api/logs/export?format_type=csv")
            
            if response.status_code == 200:
                print("✅ CSV export successful")
                print(f"   Content Type: {response.headers.get('content-type', 'N/A')}")
                print(f"   Content Length: {len(response.content)} bytes")
                
                # Check CSV format
                content = response.text
                lines = content.split('\n')
                if len(lines) > 0 and 'timestamp' in lines[0]:
                    print("   ✅ Valid CSV format confirmed")
                    print(f"   Headers: {lines[0]}")
                    print(f"   Data Rows: {len(lines) - 1}")
                else:
                    print("   ⚠️ CSV format may be invalid")
            else:
                print(f"❌ CSV export failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error with CSV export: {e}")
    
    def demonstrate_maintenance_operations(self):
        """Demonstrate maintenance and cleanup operations"""
        print("\n🧹 Testing Maintenance Operations")
        print("-" * 40)
        
        # Test cleanup (dry run - don't actually delete)
        print("\n📋 Cleanup Operation (Dry Run)")
        try:
            # First try without confirmation (should fail)
            response = self.session.delete(f"{self.base_url}/api/logs/cleanup?days_to_keep=30")
            
            if response.status_code == 400:
                print("✅ Cleanup protection working - confirmation required")
                error_detail = response.json().get("detail", "")
                if "confirmation" in error_detail:
                    print("   ✅ Proper confirmation check in place")
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing cleanup protection: {e}")
        
        # Show what cleanup would do (with confirmation)
        print("\n📋 Cleanup with Confirmation")
        try:
            response = self.session.delete(f"{self.base_url}/api/logs/cleanup?days_to_keep=1&confirm=true")
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    print("✅ Cleanup operation completed")
                    print(f"   Deleted Logs: {data['deleted_logs']}")
                    print(f"   Deleted Alerts: {data['deleted_alerts']}")
                    print(f"   Days Kept: {data['days_kept']}")
                else:
                    print(f"❌ Cleanup failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ Cleanup request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error with cleanup operation: {e}")
    
    def run_full_demo(self):
        """Run complete demonstration"""
        print("🏫 Smart Campus Access Control - Logging Service Demo")
        print("=" * 70)
        
        # Test API connection
        if not self.test_api_connection():
            print("❌ Cannot connect to API. Make sure the server is running.")
            return
        
        # Create sample data
        self.create_sample_logs()
        
        # Run all demonstrations
        self.demonstrate_log_retrieval()
        self.demonstrate_statistics()
        self.demonstrate_audit_trail()
        self.demonstrate_export_functionality()
        self.demonstrate_maintenance_operations()
        
        print("\n" + "=" * 70)
        print("🎉 Logging Service Demo Complete!")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")
        print("📊 Logs API: http://localhost:8000/api/logs/")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Logging Service Demo")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--test", choices=["logs", "stats", "audit", "export", "maintenance"], 
                       help="Run specific test")
    
    args = parser.parse_args()
    
    demo = LoggingServiceDemo(base_url=args.url)
    
    if args.test:
        if not demo.test_api_connection():
            return 1
            
        if args.test == "logs":
            demo.create_sample_logs()
            demo.demonstrate_log_retrieval()
        elif args.test == "stats":
            demo.demonstrate_statistics()
        elif args.test == "audit":
            demo.demonstrate_audit_trail()
        elif args.test == "export":
            demo.demonstrate_export_functionality()
        elif args.test == "maintenance":
            demo.demonstrate_maintenance_operations()
    else:
        demo.run_full_demo()
    
    return 0

if __name__ == "__main__":
    exit(main())