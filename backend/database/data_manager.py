#!/usr/bin/env python3
"""
Comprehensive data management utility for Smart Campus Access Control
Combines initialization, seeding, validation, and maintenance
"""

import sys
import os
import argparse
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_initialization():
    """Run database initialization"""
    print("🚀 Running database initialization...")
    from database.init_db import main as init_main
    return init_main()

def run_seeding(clear_existing=True):
    """Run mock data seeding"""
    print("🌱 Running mock data seeding...")
    from database.seed_mock_data import MockDataSeeder
    
    seeder = MockDataSeeder()
    result = seeder.seed_database(clear_existing=clear_existing)
    
    if result["success"]:
        print("✅ Mock data seeding completed successfully")
        return 0
    else:
        print(f"❌ Mock data seeding failed: {result['message']}")
        return 1

def run_validation():
    """Run data validation"""
    print("🔍 Running data validation...")
    from database.validate_data import main as validate_main
    return validate_main()

def run_demo_setup():
    """Set up demo scenarios"""
    print("🎭 Setting up demo scenarios...")
    from database.seed_mock_data import MockDataSeeder
    
    seeder = MockDataSeeder()
    result = seeder.create_demo_scenarios()
    
    if result["success"]:
        print("✅ Demo scenarios created successfully")
        return 0
    else:
        print(f"❌ Demo setup failed: {result['message']}")
        return 1

def run_full_setup():
    """Run complete setup: init + seed + validate + demo"""
    print("🏗️ Running full database setup...")
    print("=" * 50)
    
    steps = [
        ("Database Initialization", run_initialization),
        ("Mock Data Seeding", lambda: run_seeding(clear_existing=True)),
        ("Data Validation", run_validation),
        ("Demo Setup", run_demo_setup)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        result = step_func()
        
        if result != 0:
            print(f"❌ {step_name} failed with exit code {result}")
            return result
        else:
            print(f"✅ {step_name} completed successfully")
    
    print("\n🎉 Full database setup completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Start the FastAPI backend: python main.py")
    print("   2. Run the Flutter app: flutter run")
    print("   3. Open web dashboard: web-dashboard/index.html")
    print("\n💡 Management commands:")
    print("   python database/manage_db.py status")
    print("   python database/manage_db.py logs")
    print("   python database/manage_db.py alerts")
    
    return 0

def run_maintenance():
    """Run database maintenance tasks"""
    print("🧹 Running database maintenance...")
    
    try:
        from database.connection import get_db_session
        from repositories import AccessLogRepository, AlertRepository
        
        with get_db_session() as db:
            access_repo = AccessLogRepository(db)
            alert_repo = AlertRepository(db)
            
            # Clean old logs (keep 90 days)
            old_logs = access_repo.cleanup_old_logs(days_to_keep=90)
            print(f"🗑️ Cleaned {old_logs} old access logs")
            
            # Clean old resolved alerts (keep 30 days)
            old_alerts = alert_repo.cleanup_old_alerts(days_to_keep=30)
            print(f"🗑️ Cleaned {old_alerts} old resolved alerts")
            
            print("✅ Database maintenance completed")
            return 0
            
    except Exception as e:
        print(f"❌ Maintenance failed: {e}")
        return 1

def run_status_check():
    """Run comprehensive status check"""
    print("📊 Running status check...")
    
    try:
        from database.connection import get_db_session, health_check
        from services.database_service import DatabaseService
        
        # Database health check
        db_health = health_check()
        print(f"Database Status: {'✅ Healthy' if db_health['status'] == 'healthy' else '❌ Unhealthy'}")
        
        if db_health['status'] == 'healthy':
            print("Table Counts:")
            for table, count in db_health['tables'].items():
                print(f"  - {table}: {count}")
        
        # Service health check
        with get_db_session() as db:
            db_service = DatabaseService(db)
            system_health = db_service.get_system_health()
            
            print(f"\nSystem Status: {'✅ Healthy' if system_health['status'] == 'healthy' else '❌ Unhealthy'}")
            
            if system_health['status'] == 'healthy':
                dashboard_data = db_service.get_dashboard_data(days=7)
                stats = dashboard_data['access_statistics']
                
                print(f"\nLast 7 Days Statistics:")
                print(f"  - Total Access Attempts: {stats['total_attempts']}")
                print(f"  - Access Granted: {stats['granted_count']}")
                print(f"  - Access Denied: {stats['denied_count']}")
                print(f"  - Success Rate: {stats['success_rate']}%")
                print(f"  - Active Alerts: {len(dashboard_data['active_alerts'])}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return 1

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Smart Campus Access Control - Data Manager')
    parser.add_argument('command', choices=[
        'init', 'seed', 'validate', 'demo', 'full-setup', 'maintenance', 'status'
    ], help='Command to execute')
    
    parser.add_argument('--keep-data', action='store_true', 
                       help='Keep existing data when seeding (default: clear existing)')
    
    args = parser.parse_args()
    
    print("🏫 Smart Campus Access Control - Data Manager")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        if args.command == 'init':
            return run_initialization()
            
        elif args.command == 'seed':
            return run_seeding(clear_existing=not args.keep_data)
            
        elif args.command == 'validate':
            return run_validation()
            
        elif args.command == 'demo':
            return run_demo_setup()
            
        elif args.command == 'full-setup':
            return run_full_setup()
            
        elif args.command == 'maintenance':
            return run_maintenance()
            
        elif args.command == 'status':
            return run_status_check()
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())