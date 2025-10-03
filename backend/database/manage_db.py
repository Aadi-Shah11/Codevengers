#!/usr/bin/env python3
"""
Database management utility for Smart Campus Access Control
Provides commands for database operations, maintenance, and testing
"""

import mysql.connector
from mysql.connector import Error
import argparse
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Change this to your MySQL root password
    'database': 'campus_access_control',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

class DatabaseManager:
    def __init__(self):
        self.connection = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                print("✅ Connected to database")
                return True
        except Error as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("📴 Database connection closed")
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute SQL query"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
                cursor.close()
                return result
            else:
                self.connection.commit()
                cursor.close()
                return True
                
        except Error as e:
            print(f"❌ Query execution failed: {e}")
            return None
    
    def show_tables(self):
        """Display all tables with record counts"""
        print("\n📋 Database Tables:")
        tables_query = "SHOW TABLES"
        tables = self.execute_query(tables_query, fetch=True)
        
        if tables:
            for table in tables:
                table_name = list(table.values())[0]
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                count_result = self.execute_query(count_query, fetch=True)
                count = count_result[0]['count'] if count_result else 0
                print(f"  - {table_name}: {count} records")
    
    def show_recent_logs(self, limit=10):
        """Display recent access logs"""
        print(f"\n📊 Recent Access Logs (Last {limit}):")
        query = """
        SELECT timestamp, gate_id, user_id, license_plate, 
               verification_method, access_granted, alert_triggered
        FROM access_logs 
        ORDER BY timestamp DESC 
        LIMIT %s
        """
        logs = self.execute_query(query, (limit,), fetch=True)
        
        if logs:
            for log in logs:
                status = "✅ GRANTED" if log['access_granted'] else "❌ DENIED"
                alert = " 🚨 ALERT" if log['alert_triggered'] else ""
                print(f"  {log['timestamp']} | {log['gate_id']} | {status}{alert}")
                print(f"    ID: {log['user_id'] or 'N/A'} | Plate: {log['license_plate'] or 'N/A'} | Method: {log['verification_method']}")
        else:
            print("  No logs found")
    
    def show_active_alerts(self):
        """Display active security alerts"""
        print("\n🚨 Active Security Alerts:")
        query = """
        SELECT alert_type, message, user_id, license_plate, 
               gate_id, created_at
        FROM alerts 
        WHERE resolved = FALSE 
        ORDER BY created_at DESC
        """
        alerts = self.execute_query(query, fetch=True)
        
        if alerts:
            for alert in alerts:
                print(f"  🔴 {alert['alert_type'].upper()}: {alert['message']}")
                print(f"    Gate: {alert['gate_id']} | Time: {alert['created_at']}")
        else:
            print("  ✅ No active alerts")
    
    def get_statistics(self, days=7):
        """Get access statistics for specified days"""
        print(f"\n📈 Access Statistics (Last {days} days):")
        
        # Overall stats
        query = """
        SELECT 
            COUNT(*) as total_attempts,
            SUM(CASE WHEN access_granted = TRUE THEN 1 ELSE 0 END) as granted,
            SUM(CASE WHEN access_granted = FALSE THEN 1 ELSE 0 END) as denied,
            SUM(CASE WHEN alert_triggered = TRUE THEN 1 ELSE 0 END) as alerts,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT license_plate) as unique_vehicles
        FROM access_logs 
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        stats = self.execute_query(query, (days,), fetch=True)
        
        if stats and stats[0]['total_attempts'] > 0:
            s = stats[0]
            success_rate = (s['granted'] / s['total_attempts']) * 100
            print(f"  Total Attempts: {s['total_attempts']}")
            print(f"  Access Granted: {s['granted']} ({success_rate:.1f}%)")
            print(f"  Access Denied: {s['denied']}")
            print(f"  Security Alerts: {s['alerts']}")
            print(f"  Unique Users: {s['unique_users']}")
            print(f"  Unique Vehicles: {s['unique_vehicles']}")
        else:
            print("  No access attempts in the specified period")
    
    def test_user_verification(self, user_id):
        """Test user ID verification"""
        print(f"\n🔍 Testing User Verification: {user_id}")
        query = """
        SELECT id, name, role, department, status 
        FROM users 
        WHERE id = %s
        """
        result = self.execute_query(query, (user_id,), fetch=True)
        
        if result:
            user = result[0]
            status = "✅ VALID" if user['status'] == 'active' else "❌ INACTIVE"
            print(f"  {status}: {user['name']} ({user['role']}, {user['department']})")
        else:
            print(f"  ❌ INVALID: User {user_id} not found")
    
    def test_vehicle_verification(self, license_plate):
        """Test vehicle verification"""
        print(f"\n🚗 Testing Vehicle Verification: {license_plate}")
        query = """
        SELECT v.license_plate, v.owner_id, u.name, v.vehicle_type, 
               v.color, v.model, v.status
        FROM vehicles v
        LEFT JOIN users u ON v.owner_id = u.id
        WHERE v.license_plate = %s
        """
        result = self.execute_query(query, (license_plate,), fetch=True)
        
        if result:
            vehicle = result[0]
            status = "✅ VALID" if vehicle['status'] == 'active' else "❌ INACTIVE"
            print(f"  {status}: {vehicle['vehicle_type']} ({vehicle['color']} {vehicle['model']})")
            print(f"  Owner: {vehicle['name']} ({vehicle['owner_id']})")
        else:
            print(f"  ❌ INVALID: Vehicle {license_plate} not found")
    
    def simulate_access_attempt(self, user_id=None, license_plate=None, gate_id="MAIN_GATE"):
        """Simulate an access attempt for testing"""
        print(f"\n🎭 Simulating Access Attempt:")
        print(f"  Gate: {gate_id}")
        print(f"  User ID: {user_id or 'None'}")
        print(f"  License Plate: {license_plate or 'None'}")
        
        # Determine verification method
        if user_id and license_plate:
            method = 'both'
        elif user_id:
            method = 'id_only'
        elif license_plate:
            method = 'vehicle_only'
        else:
            print("  ❌ Error: Must provide either user_id or license_plate")
            return
        
        # Check user validity
        user_valid = False
        if user_id:
            user_result = self.execute_query(
                "SELECT COUNT(*) as count FROM users WHERE id = %s AND status = 'active'",
                (user_id,), fetch=True
            )
            user_valid = user_result[0]['count'] > 0 if user_result else False
        
        # Check vehicle validity
        vehicle_valid = False
        if license_plate:
            vehicle_result = self.execute_query(
                "SELECT COUNT(*) as count FROM vehicles WHERE license_plate = %s AND status = 'active'",
                (license_plate,), fetch=True
            )
            vehicle_valid = vehicle_result[0]['count'] > 0 if vehicle_result else False
        
        # Determine access decision (grant if either is valid)
        access_granted = user_valid or vehicle_valid
        
        # Log the attempt
        log_query = """
        INSERT INTO access_logs (gate_id, user_id, license_plate, verification_method, 
                               access_granted, alert_triggered, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        alert_triggered = not access_granted
        notes = f"Simulated access attempt - User valid: {user_valid}, Vehicle valid: {vehicle_valid}"
        
        success = self.execute_query(log_query, (
            gate_id, user_id, license_plate, method, 
            access_granted, alert_triggered, notes
        ))
        
        if success:
            result = "✅ ACCESS GRANTED" if access_granted else "❌ ACCESS DENIED"
            print(f"  Result: {result}")
            print(f"  Method: {method}")
            print(f"  Alert Triggered: {alert_triggered}")
            
            # Create alert if access denied
            if alert_triggered:
                alert_query = """
                INSERT INTO alerts (alert_type, message, user_id, license_plate, gate_id)
                VALUES (%s, %s, %s, %s, %s)
                """
                alert_type = 'unauthorized_id' if user_id else 'unauthorized_vehicle'
                message = f"Simulated unauthorized access attempt at {gate_id}"
                
                self.execute_query(alert_query, (alert_type, message, user_id, license_plate, gate_id))
                print("  🚨 Security alert created")
        else:
            print("  ❌ Failed to log access attempt")
    
    def cleanup_old_data(self, days_to_keep=30):
        """Clean up old logs and resolved alerts"""
        print(f"\n🧹 Cleaning up data older than {days_to_keep} days...")
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Delete old access logs
        logs_query = "DELETE FROM access_logs WHERE timestamp < %s"
        logs_deleted = self.execute_query(logs_query, (cutoff_date,))
        
        # Delete old resolved alerts
        alerts_query = "DELETE FROM alerts WHERE resolved = TRUE AND created_at < %s"
        alerts_deleted = self.execute_query(alerts_query, (cutoff_date,))
        
        if logs_deleted and alerts_deleted:
            print(f"  ✅ Cleanup completed")
            print(f"  Cutoff date: {cutoff_date.strftime('%Y-%m-%d')}")
        else:
            print("  ❌ Cleanup failed")

def main():
    parser = argparse.ArgumentParser(description='Smart Campus Access Control Database Manager')
    parser.add_argument('command', choices=[
        'status', 'logs', 'alerts', 'stats', 'test-user', 'test-vehicle', 
        'simulate', 'cleanup', 'init', 'seed', 'validate', 'demo'
    ], help='Command to execute')
    
    parser.add_argument('--user-id', help='User ID for testing')
    parser.add_argument('--license-plate', help='License plate for testing')
    parser.add_argument('--gate-id', default='MAIN_GATE', help='Gate ID for simulation')
    parser.add_argument('--days', type=int, default=7, help='Number of days for statistics/cleanup')
    parser.add_argument('--limit', type=int, default=10, help='Limit for logs display')
    
    args = parser.parse_args()
    
    # Initialize database manager
    db = DatabaseManager()
    
    if not db.connect():
        sys.exit(1)
    
    try:
        if args.command == 'status':
            db.show_tables()
            
        elif args.command == 'logs':
            db.show_recent_logs(args.limit)
            
        elif args.command == 'alerts':
            db.show_active_alerts()
            
        elif args.command == 'stats':
            db.get_statistics(args.days)
            
        elif args.command == 'test-user':
            if not args.user_id:
                print("❌ --user-id required for user testing")
                sys.exit(1)
            db.test_user_verification(args.user_id)
            
        elif args.command == 'test-vehicle':
            if not args.license_plate:
                print("❌ --license-plate required for vehicle testing")
                sys.exit(1)
            db.test_vehicle_verification(args.license_plate)
            
        elif args.command == 'simulate':
            if not args.user_id and not args.license_plate:
                print("❌ Either --user-id or --license-plate required for simulation")
                sys.exit(1)
            db.simulate_access_attempt(args.user_id, args.license_plate, args.gate_id)
            
        elif args.command == 'cleanup':
            db.cleanup_old_data(args.days)
            
        elif args.command == 'init':
            print("🚀 Use init_db.py for database initialization")
            
        elif args.command == 'seed':
            print("🌱 Use seed_mock_data.py for comprehensive data seeding")
            print("   python database/seed_mock_data.py")
            
        elif args.command == 'validate':
            print("🔍 Use validate_data.py for data validation")
            print("   python database/validate_data.py")
            
        elif args.command == 'demo':
            print("🎭 Creating demo scenarios...")
            # Import and run demo creation
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from database.seed_mock_data import MockDataSeeder
                
                seeder = MockDataSeeder()
                result = seeder.create_demo_scenarios()
                
                if result["success"]:
                    print("✅ Demo scenarios created successfully")
                    for scenario in result["scenarios"]:
                        print(f"   - {scenario}")
                else:
                    print(f"❌ Failed to create demo scenarios: {result['message']}")
                    
            except Exception as e:
                print(f"❌ Error creating demo scenarios: {e}")
            
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()