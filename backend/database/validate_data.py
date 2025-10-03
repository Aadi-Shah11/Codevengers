#!/usr/bin/env python3
"""
Data validation script for Smart Campus Access Control
Validates data integrity and relationships
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_session
from models import User, Vehicle, AccessLog, Alert, UserStatus, VehicleStatus
from services.database_service import DatabaseService

class DataValidator:
    """
    Validates database data integrity and relationships
    """
    
    def __init__(self):
        self.validation_results = []
        self.errors = []
        self.warnings = []
    
    def validate_users(self, db) -> Dict[str, Any]:
        """Validate user data"""
        print("👥 Validating users...")
        
        users = db.query(User).all()
        
        # Check for required fields
        users_missing_data = []
        for user in users:
            if not user.name or not user.role:
                users_missing_data.append(user.id)
        
        # Check for duplicate emails
        emails = [user.email for user in users if user.email]
        duplicate_emails = [email for email in set(emails) if emails.count(email) > 1]
        
        # Check role distribution
        role_counts = {}
        status_counts = {}
        for user in users:
            role_counts[user.role.value] = role_counts.get(user.role.value, 0) + 1
            status_counts[user.status.value] = status_counts.get(user.status.value, 0) + 1
        
        result = {
            "total_users": len(users),
            "missing_data": users_missing_data,
            "duplicate_emails": duplicate_emails,
            "role_distribution": role_counts,
            "status_distribution": status_counts,
            "validation_passed": len(users_missing_data) == 0 and len(duplicate_emails) == 0
        }
        
        if not result["validation_passed"]:
            if users_missing_data:
                self.errors.append(f"Users with missing data: {users_missing_data}")
            if duplicate_emails:
                self.errors.append(f"Duplicate emails found: {duplicate_emails}")
        
        return result
    
    def validate_vehicles(self, db) -> Dict[str, Any]:
        """Validate vehicle data"""
        print("🚗 Validating vehicles...")
        
        vehicles = db.query(Vehicle).all()
        
        # Check for orphaned vehicles (owner doesn't exist)
        orphaned_vehicles = []
        for vehicle in vehicles:
            if vehicle.owner_id:
                owner = db.query(User).filter(User.id == vehicle.owner_id).first()
                if not owner:
                    orphaned_vehicles.append(vehicle.license_plate)
        
        # Check for vehicles with inactive owners
        inactive_owner_vehicles = []
        for vehicle in vehicles:
            if vehicle.owner_id:
                owner = db.query(User).filter(User.id == vehicle.owner_id).first()
                if owner and owner.status == UserStatus.INACTIVE:
                    inactive_owner_vehicles.append(vehicle.license_plate)
        
        # Check vehicle type distribution
        type_counts = {}
        status_counts = {}
        for vehicle in vehicles:
            type_counts[vehicle.vehicle_type.value] = type_counts.get(vehicle.vehicle_type.value, 0) + 1
            status_counts[vehicle.status.value] = status_counts.get(vehicle.status.value, 0) + 1
        
        result = {
            "total_vehicles": len(vehicles),
            "orphaned_vehicles": orphaned_vehicles,
            "inactive_owner_vehicles": inactive_owner_vehicles,
            "type_distribution": type_counts,
            "status_distribution": status_counts,
            "validation_passed": len(orphaned_vehicles) == 0
        }
        
        if orphaned_vehicles:
            self.errors.append(f"Orphaned vehicles (no owner): {orphaned_vehicles}")
        
        if inactive_owner_vehicles:
            self.warnings.append(f"Vehicles with inactive owners: {inactive_owner_vehicles}")
        
        return result
    
    def validate_access_logs(self, db) -> Dict[str, Any]:
        """Validate access log data"""
        print("📋 Validating access logs...")
        
        logs = db.query(AccessLog).all()
        
        # Check for logs with invalid references
        invalid_user_logs = []
        invalid_vehicle_logs = []
        
        for log in logs:
            if log.user_id:
                user = db.query(User).filter(User.id == log.user_id).first()
                if not user:
                    invalid_user_logs.append(log.id)
            
            if log.license_plate:
                vehicle = db.query(Vehicle).filter(Vehicle.license_plate == log.license_plate).first()
                if not vehicle:
                    invalid_vehicle_logs.append(log.id)
        
        # Check verification method consistency
        inconsistent_logs = []
        for log in logs:
            has_user = log.user_id is not None
            has_vehicle = log.license_plate is not None
            
            if log.verification_method.value == "both" and not (has_user and has_vehicle):
                inconsistent_logs.append(log.id)
            elif log.verification_method.value == "id_only" and not has_user:
                inconsistent_logs.append(log.id)
            elif log.verification_method.value == "vehicle_only" and not has_vehicle:
                inconsistent_logs.append(log.id)
        
        # Check access patterns
        recent_logs = db.query(AccessLog).filter(
            AccessLog.timestamp >= datetime.now() - timedelta(days=7)
        ).all()
        
        granted_count = sum(1 for log in recent_logs if log.access_granted)
        denied_count = len(recent_logs) - granted_count
        success_rate = (granted_count / len(recent_logs) * 100) if recent_logs else 0
        
        result = {
            "total_logs": len(logs),
            "recent_logs": len(recent_logs),
            "invalid_user_references": invalid_user_logs,
            "invalid_vehicle_references": invalid_vehicle_logs,
            "inconsistent_verification": inconsistent_logs,
            "success_rate": round(success_rate, 2),
            "granted_count": granted_count,
            "denied_count": denied_count,
            "validation_passed": len(invalid_user_logs) == 0 and len(invalid_vehicle_logs) == 0 and len(inconsistent_logs) == 0
        }
        
        if invalid_user_logs:
            self.errors.append(f"Logs with invalid user references: {invalid_user_logs}")
        if invalid_vehicle_logs:
            self.errors.append(f"Logs with invalid vehicle references: {invalid_vehicle_logs}")
        if inconsistent_logs:
            self.errors.append(f"Logs with inconsistent verification methods: {inconsistent_logs}")
        
        return result
    
    def validate_alerts(self, db) -> Dict[str, Any]:
        """Validate alert data"""
        print("🚨 Validating alerts...")
        
        alerts = db.query(Alert).all()
        
        # Check for alerts with invalid references
        invalid_user_alerts = []
        invalid_vehicle_alerts = []
        
        for alert in alerts:
            if alert.user_id:
                user = db.query(User).filter(User.id == alert.user_id).first()
                if not user:
                    invalid_user_alerts.append(alert.id)
            
            if alert.license_plate:
                vehicle = db.query(Vehicle).filter(Vehicle.license_plate == alert.license_plate).first()
                if not vehicle:
                    invalid_vehicle_alerts.append(alert.id)
        
        # Check alert resolution consistency
        inconsistent_resolution = []
        for alert in alerts:
            if alert.resolved and not alert.resolved_at:
                inconsistent_resolution.append(alert.id)
            elif not alert.resolved and alert.resolved_at:
                inconsistent_resolution.append(alert.id)
        
        # Alert statistics
        active_alerts = [alert for alert in alerts if not alert.resolved]
        resolved_alerts = [alert for alert in alerts if alert.resolved]
        
        type_counts = {}
        for alert in alerts:
            type_counts[alert.alert_type.value] = type_counts.get(alert.alert_type.value, 0) + 1
        
        result = {
            "total_alerts": len(alerts),
            "active_alerts": len(active_alerts),
            "resolved_alerts": len(resolved_alerts),
            "invalid_user_references": invalid_user_alerts,
            "invalid_vehicle_references": invalid_vehicle_alerts,
            "inconsistent_resolution": inconsistent_resolution,
            "type_distribution": type_counts,
            "validation_passed": len(invalid_user_alerts) == 0 and len(invalid_vehicle_alerts) == 0 and len(inconsistent_resolution) == 0
        }
        
        if invalid_user_alerts:
            self.errors.append(f"Alerts with invalid user references: {invalid_user_alerts}")
        if invalid_vehicle_alerts:
            self.errors.append(f"Alerts with invalid vehicle references: {invalid_vehicle_alerts}")
        if inconsistent_resolution:
            self.errors.append(f"Alerts with inconsistent resolution status: {inconsistent_resolution}")
        
        return result
    
    def validate_business_logic(self, db) -> Dict[str, Any]:
        """Validate business logic consistency"""
        print("🔍 Validating business logic...")
        
        # Check if denied access logs have corresponding alerts
        denied_logs = db.query(AccessLog).filter(AccessLog.access_granted == False).all()
        logs_without_alerts = []
        
        for log in denied_logs:
            if not log.alert_triggered:
                continue
            
            # Look for corresponding alert
            alert_found = False
            alerts = db.query(Alert).filter(
                Alert.created_at >= log.timestamp - timedelta(minutes=5),
                Alert.created_at <= log.timestamp + timedelta(minutes=5)
            ).all()
            
            for alert in alerts:
                if (alert.user_id == log.user_id and log.user_id) or \
                   (alert.license_plate == log.license_plate and log.license_plate):
                    alert_found = True
                    break
            
            if not alert_found:
                logs_without_alerts.append(log.id)
        
        # Check for active users with inactive vehicles
        active_users_inactive_vehicles = []
        active_users = db.query(User).filter(User.status == UserStatus.ACTIVE).all()
        
        for user in active_users:
            vehicles = db.query(Vehicle).filter(Vehicle.owner_id == user.id).all()
            if vehicles and all(v.status == VehicleStatus.INACTIVE for v in vehicles):
                active_users_inactive_vehicles.append(user.id)
        
        result = {
            "denied_logs_without_alerts": logs_without_alerts,
            "active_users_inactive_vehicles": active_users_inactive_vehicles,
            "validation_passed": len(logs_without_alerts) == 0
        }
        
        if logs_without_alerts:
            self.warnings.append(f"Denied access logs without corresponding alerts: {logs_without_alerts}")
        
        if active_users_inactive_vehicles:
            self.warnings.append(f"Active users with only inactive vehicles: {active_users_inactive_vehicles}")
        
        return result
    
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete data validation"""
        print("🔍 Starting comprehensive data validation...")
        print("=" * 50)
        
        try:
            with get_db_session() as db:
                # Run all validations
                user_validation = self.validate_users(db)
                vehicle_validation = self.validate_vehicles(db)
                log_validation = self.validate_access_logs(db)
                alert_validation = self.validate_alerts(db)
                business_validation = self.validate_business_logic(db)
                
                # Overall validation status
                all_passed = all([
                    user_validation["validation_passed"],
                    vehicle_validation["validation_passed"],
                    log_validation["validation_passed"],
                    alert_validation["validation_passed"],
                    business_validation["validation_passed"]
                ])
                
                result = {
                    "overall_status": "PASSED" if all_passed else "FAILED",
                    "validation_timestamp": datetime.now().isoformat(),
                    "validations": {
                        "users": user_validation,
                        "vehicles": vehicle_validation,
                        "access_logs": log_validation,
                        "alerts": alert_validation,
                        "business_logic": business_validation
                    },
                    "errors": self.errors,
                    "warnings": self.warnings,
                    "summary": {
                        "total_users": user_validation["total_users"],
                        "total_vehicles": vehicle_validation["total_vehicles"],
                        "total_logs": log_validation["total_logs"],
                        "total_alerts": alert_validation["total_alerts"],
                        "error_count": len(self.errors),
                        "warning_count": len(self.warnings)
                    }
                }
                
                # Print results
                print("\n📊 Validation Summary:")
                print(f"Overall Status: {'✅ PASSED' if all_passed else '❌ FAILED'}")
                print(f"Users: {user_validation['total_users']}")
                print(f"Vehicles: {vehicle_validation['total_vehicles']}")
                print(f"Access Logs: {log_validation['total_logs']}")
                print(f"Alerts: {alert_validation['total_alerts']}")
                print(f"Errors: {len(self.errors)}")
                print(f"Warnings: {len(self.warnings)}")
                
                if self.errors:
                    print("\n❌ Errors Found:")
                    for error in self.errors:
                        print(f"  - {error}")
                
                if self.warnings:
                    print("\n⚠️ Warnings:")
                    for warning in self.warnings:
                        print(f"  - {warning}")
                
                if all_passed and not self.warnings:
                    print("\n🎉 All validations passed! Data integrity is excellent.")
                elif all_passed:
                    print("\n✅ All critical validations passed. Review warnings for optimization.")
                else:
                    print("\n❌ Validation failed. Please fix errors before proceeding.")
                
                return result
                
        except Exception as e:
            error_result = {
                "overall_status": "ERROR",
                "error": str(e),
                "validation_timestamp": datetime.now().isoformat()
            }
            print(f"\n❌ Validation error: {e}")
            return error_result

def main():
    """Main function to run validation"""
    print("🏫 Smart Campus Access Control - Data Validator")
    print("=" * 50)
    
    validator = DataValidator()
    result = validator.run_full_validation()
    
    # Return appropriate exit code
    if result.get("overall_status") == "PASSED":
        return 0
    elif result.get("overall_status") == "FAILED":
        return 1
    else:
        return 2

if __name__ == "__main__":
    exit(main())