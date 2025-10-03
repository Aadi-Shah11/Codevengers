#!/usr/bin/env python3
"""
API testing utility for Smart Campus Access Control
Tests all API endpoints with sample data
"""

import requests
import json
import time
from typing import Dict, Any

class APITester:
    """
    Comprehensive API testing utility
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def test_endpoint(self, method: str, endpoint: str, data: Dict[Any, Any] = None, 
                     files: Dict[str, Any] = None, expected_status: int = 200) -> Dict[str, Any]:
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, params=data)
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(url, data=data, files=files)
                else:
                    response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "url": url,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time": round(response_time, 3),
                "success": response.status_code == expected_status,
                "response_data": None,
                "error": None
            }
            
            try:
                result["response_data"] = response.json()
            except:
                result["response_data"] = response.text
            
            
            if not result["success"]:
                result["error"] = f"Expected status {expected_status}, got {response.status_code}"
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            result = {
                "method": method.upper(),
                "endpoint": endpoint,
                "url": url,
                "status_code": None,
                "expected_status": expected_status,
                "response_time": None,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            self.test_results.append(result)
            return result
    
    def test_health_endpoints(self):
        """Test health and status endpoints"""
        print("🏥 Testing health endpoints...")
        
        # Root endpoint
        self.test_endpoint("GET", "/")
        
        # Health check
        self.test_endpoint("GET", "/health")
        
        # API status
        self.test_endpoint("GET", "/api/status")
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("🔐 Testing authentication endpoints...")
        
        # Valid ID verification
        self.test_endpoint("POST", "/api/auth/verify_id", {
            "id_number": "STU001",
            "scan_method": "manual"
        })
        
        # Invalid ID verification
        self.test_endpoint("POST", "/api/auth/verify_id", {
            "id_number": "INVALID999",
            "scan_method": "manual"
        })
        
        # Get user info
        self.test_endpoint("GET", "/api/auth/user/STU001")
        
        # List users
        self.test_endpoint("GET", "/api/auth/users", {"limit": 10})
        
        # Legacy endpoint
        self.test_endpoint("POST", "/verify_id", {
            "id_number": "STU001",
            "scan_method": "qr"
        })
    
    def test_vehicle_endpoints(self):
        """Test vehicle endpoints"""
        print("🚗 Testing vehicle endpoints...")
        
        # Register vehicle
        self.test_endpoint("POST", "/api/vehicles/register", {
            "license_plate": "TEST123",
            "owner_id": "STU001",
            "vehicle_type": "car",
            "color": "Blue",
            "model": "Test Car"
        })
        
        # Verify vehicle
        self.test_endpoint("POST", "/api/vehicles/verify/ABC123")
        
        # Get vehicle info
        self.test_endpoint("GET", "/api/vehicles/ABC123")
        
        # List vehicles
        self.test_endpoint("GET", "/api/vehicles/", {"limit": 10})
        
        # Test video upload (placeholder)
        # Note: This would need an actual video file for full testing
        print("  📹 Video upload test skipped (requires video file)")
    
    def test_logs_endpoints(self):
        """Test logs endpoints"""
        print("📋 Testing logs endpoints...")
        
        # Get access logs
        self.test_endpoint("GET", "/api/logs/", {"limit": 10})
        
        # Get recent logs
        self.test_endpoint("GET", "/api/logs/recent", {"limit": 5})
        
        # Get denied logs
        self.test_endpoint("GET", "/api/logs/denied", {"limit": 5})
        
        # Get statistics
        self.test_endpoint("GET", "/api/logs/statistics", {"days": 7})
        
        # Get patterns
        self.test_endpoint("GET", "/api/logs/patterns/hourly", {"days": 7})
        self.test_endpoint("GET", "/api/logs/patterns/daily", {"days": 30})
        
        # Search logs
        self.test_endpoint("GET", "/api/logs/search", {"q": "STU001"})
    
    def test_alerts_endpoints(self):
        """Test alerts endpoints"""
        print("🚨 Testing alerts endpoints...")
        
        # Get alerts
        self.test_endpoint("GET", "/api/alerts/", {"limit": 10})
        
        # Get recent alerts
        self.test_endpoint("GET", "/api/alerts/recent", {"hours": 24})
        
        # Get active alerts
        self.test_endpoint("GET", "/api/alerts/active")
        
        # Get critical alerts
        self.test_endpoint("GET", "/api/alerts/critical")
        
        # Get statistics
        self.test_endpoint("GET", "/api/alerts/statistics", {"days": 7})
        
        # Get trends
        self.test_endpoint("GET", "/api/alerts/trends", {"days": 30})
        
        # Search alerts
        self.test_endpoint("GET", "/api/alerts/search", {"q": "unauthorized"})
    
    def test_dashboard_endpoints(self):
        """Test dashboard endpoints"""
        print("📊 Testing dashboard endpoints...")
        
        # Get dashboard data
        self.test_endpoint("GET", "/api/dashboard/", {"days": 7})
        
        # Get summary
        self.test_endpoint("GET", "/api/dashboard/summary")
        
        # Get analytics
        self.test_endpoint("GET", "/api/dashboard/analytics", {"period": "week"})
        
        # Get live data
        self.test_endpoint("GET", "/api/dashboard/live")
        
        # Get gate statistics
        self.test_endpoint("GET", "/api/dashboard/gates", {"days": 7})
        
        # Search dashboard
        self.test_endpoint("GET", "/api/dashboard/search", {"q": "STU001"})
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🧪 Starting comprehensive API tests...")
        print("=" * 50)
        
        start_time = time.time()
        
        # Test all endpoint groups
        self.test_health_endpoints()
        self.test_auth_endpoints()
        self.test_vehicle_endpoints()
        self.test_logs_endpoints()
        self.test_alerts_endpoints()
        self.test_dashboard_endpoints()
        
        total_time = time.time() - start_time
        
        # Generate report
        self.generate_report(total_time)
    
    def generate_report(self, total_time: float):
        """Generate test report"""
        print("\n" + "=" * 50)
        print("📋 API Test Report")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(successful_tests/total_tests*100):.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests ({failed_tests}):")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['method']} {result['endpoint']}: {result['error']}")
        
        # Performance summary
        response_times = [r["response_time"] for r in self.test_results if r["response_time"]]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⚡ Performance:")
            print(f"  - Average Response Time: {avg_time:.3f}s")
            print(f"  - Slowest Response: {max_time:.3f}s")
        
        print(f"\n🎯 API Base URL: {self.base_url}")
        print("📚 API Documentation: http://localhost:8000/docs")

def main():
    """Main function to run API tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Campus Access Control API Tester")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--endpoint", help="Test specific endpoint")
    
    args = parser.parse_args()
    
    tester = APITester(base_url=args.url)
    
    if args.endpoint:
        # Test specific endpoint
        result = tester.test_endpoint("GET", args.endpoint)
        print(f"Result: {result}")
    else:
        # Run all tests
        tester.run_all_tests()

if __name__ == "__main__":
    main()