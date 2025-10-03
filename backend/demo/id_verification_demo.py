#!/usr/bin/env python3
"""
ID Verification Demo Script
Demonstrates the ID verification endpoint functionality
"""

import requests
import json
import time
import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class IDVerificationDemo:
    """
    Demonstration of ID verification functionality
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
    
    def verify_id(self, user_id: str, scan_method: str = "manual", gate_id: str = "MAIN_GATE"):
        """Verify a user ID"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/verify_id",
                json={
                    "id_number": user_id,
                    "scan_method": scan_method
                },
                params={"gate_id": gate_id}
            )
            
            return response.json()
            
        except Exception as e:
            return {"error": str(e)}
    
    def demonstrate_valid_verification(self):
        """Demonstrate successful ID verification"""
        print("\n🔍 Testing Valid ID Verification")
        print("-" * 40)
        
        test_cases = [
            {"id": "STU001", "method": "manual", "description": "Student - Manual Entry"},
            {"id": "STF001", "method": "qr", "description": "Staff - QR Code Scan"},
            {"id": "FAC001", "method": "barcode", "description": "Faculty - Barcode Scan"}
        ]
        
        for case in test_cases:
            print(f"\n📋 {case['description']}")
            result = self.verify_id(case["id"], case["method"])
            
            if result.get("access_granted"):
                print(f"✅ Access GRANTED for {case['id']}")
                print(f"   User: {result.get('user_name')} ({result.get('user_role')})")
                print(f"   Department: {result.get('user_department')}")
                print(f"   Security Level: {result.get('security_level')}")
                print(f"   Log ID: {result.get('log_id')}")
            else:
                print(f"❌ Access DENIED for {case['id']}")
                print(f"   Reason: {result.get('message')}")
    
    def demonstrate_invalid_verification(self):
        """Demonstrate failed ID verification scenarios"""
        print("\n🚫 Testing Invalid ID Verification")
        print("-" * 40)
        
        test_cases = [
            {"id": "INVALID999", "description": "Non-existent User ID"},
            {"id": "STU005", "description": "Inactive User Account"},
            {"id": "HACK123", "description": "Suspicious ID Pattern"},
            {"id": "", "description": "Empty ID"},
            {"id": "AB", "description": "Too Short ID"}
        ]
        
        for case in test_cases:
            print(f"\n📋 {case['description']}")
            result = self.verify_id(case["id"])
            
            print(f"❌ Access DENIED for '{case['id']}'")
            print(f"   Reason: {result.get('message', 'Unknown error')}")
            print(f"   Error Code: {result.get('error_code', 'N/A')}")
            
            if result.get("alert_ids"):
                print(f"   🚨 Security Alert Generated: {result['alert_ids']}")
    
    def demonstrate_scan_methods(self):
        """Demonstrate different scanning methods"""
        print("\n📱 Testing Different Scan Methods")
        print("-" * 40)
        
        scan_methods = ["manual", "qr", "barcode"]
        user_id = "STU001"
        
        for method in scan_methods:
            print(f"\n📋 Scan Method: {method.upper()}")
            result = self.verify_id(user_id, method)
            
            if result.get("access_granted"):
                print(f"✅ {method.upper()} scan successful")
                print(f"   Response Time: {result.get('timestamp')}")
                print(f"   Method Recorded: {result.get('scan_method')}")
            else:
                print(f"❌ {method.upper()} scan failed")
    
    def demonstrate_security_features(self):
        """Demonstrate security features"""
        print("\n🔒 Testing Security Features")
        print("-" * 40)
        
        # Test rate limiting simulation
        print("\n📋 Rapid Access Attempts (Rate Limiting Test)")
        user_id = "STU001"
        
        for i in range(3):
            result = self.verify_id(user_id)
            print(f"   Attempt {i+1}: {'✅ Success' if result.get('access_granted') else '❌ Failed'}")
            time.sleep(0.5)  # Small delay
        
        # Test suspicious patterns
        print("\n📋 Suspicious Pattern Detection")
        suspicious_ids = ["HACK001", "ADMIN999", "TEST123"]
        
        for suspicious_id in suspicious_ids:
            result = self.verify_id(suspicious_id)
            print(f"   {suspicious_id}: {'🚨 Blocked' if result.get('error_code') == 'SUSPICIOUS_PATTERN' else '⚠️ Not blocked'}")
    
    def demonstrate_comprehensive_verification(self):
        """Demonstrate comprehensive access verification"""
        print("\n🔄 Testing Comprehensive Access Verification")
        print("-" * 40)
        
        try:
            # Test ID-only verification
            response = self.session.post(
                f"{self.base_url}/api/auth/verify_access",
                params={
                    "user_id": "STU001",
                    "gate_id": "MAIN_GATE",
                    "scan_method": "manual"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Comprehensive verification successful")
                print(f"   Access Granted: {result.get('access_granted')}")
                print(f"   Verification Method: {result.get('verification_method')}")
                print(f"   Security Level: {result.get('security_level')}")
                print(f"   Decision Reason: {result.get('decision_reason')}")
            else:
                print(f"❌ Comprehensive verification failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in comprehensive verification: {e}")
    
    def get_verification_statistics(self):
        """Get and display verification statistics"""
        print("\n📊 Verification Statistics")
        print("-" * 40)
        
        try:
            response = self.session.get(f"{self.base_url}/api/auth/verification/statistics?days=7")
            
            if response.status_code == 200:
                stats = response.json()
                
                print(f"📈 Last 7 Days Statistics:")
                access_stats = stats.get("access_statistics", {})
                print(f"   Total Attempts: {access_stats.get('total_attempts', 0)}")
                print(f"   Success Rate: {access_stats.get('success_rate', 0)}%")
                print(f"   Unique Users: {access_stats.get('unique_users', 0)}")
                
                method_stats = stats.get("verification_methods", {})
                print(f"\n📱 Verification Methods:")
                for method, count in method_stats.items():
                    print(f"   {method.replace('_', ' ').title()}: {count}")
                
                security_stats = stats.get("security_levels", {})
                print(f"\n🔒 Security Levels:")
                for level, count in security_stats.items():
                    print(f"   {level.replace('_', ' ').title()}: {count}")
            else:
                print(f"❌ Failed to get statistics: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
    
    def run_full_demo(self):
        """Run complete demonstration"""
        print("🏫 Smart Campus Access Control - ID Verification Demo")
        print("=" * 60)
        
        # Test API connection
        if not self.test_api_connection():
            print("❌ Cannot connect to API. Make sure the server is running.")
            return
        
        # Run all demonstrations
        self.demonstrate_valid_verification()
        self.demonstrate_invalid_verification()
        self.demonstrate_scan_methods()
        self.demonstrate_security_features()
        self.demonstrate_comprehensive_verification()
        self.get_verification_statistics()
        
        print("\n" + "=" * 60)
        print("🎉 ID Verification Demo Complete!")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔍 Health Check: http://localhost:8000/health")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ID Verification Demo")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--test", choices=["valid", "invalid", "methods", "security", "stats"], 
                       help="Run specific test")
    
    args = parser.parse_args()
    
    demo = IDVerificationDemo(base_url=args.url)
    
    if args.test:
        if not demo.test_api_connection():
            return 1
            
        if args.test == "valid":
            demo.demonstrate_valid_verification()
        elif args.test == "invalid":
            demo.demonstrate_invalid_verification()
        elif args.test == "methods":
            demo.demonstrate_scan_methods()
        elif args.test == "security":
            demo.demonstrate_security_features()
        elif args.test == "stats":
            demo.get_verification_statistics()
    else:
        demo.run_full_demo()
    
    return 0

if __name__ == "__main__":
    exit(main())