#!/usr/bin/env python3
"""
Startup script for Smart Campus Access Control API
Handles initialization, health checks, and graceful startup
"""

import sys
import os
import time
import subprocess
import signal
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("📦 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import pymysql
        print("✅ Core dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_database():
    """Check database connection"""
    print("🗄️ Checking database connection...")
    
    try:
        from database.connection import check_connection
        if check_connection():
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database check error: {e}")
        return False

def initialize_database():
    """Initialize database if needed"""
    print("🔧 Initializing database...")
    
    try:
        from database.connection import create_tables
        create_tables()
        print("✅ Database tables verified")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def seed_database_if_empty():
    """Seed database with mock data if it's empty"""
    print("🌱 Checking if database needs seeding...")
    
    try:
        from database.connection import get_db_session
        from models import User
        
        with get_db_session() as db:
            user_count = db.query(User).count()
            
            if user_count == 0:
                print("📊 Database is empty, seeding with mock data...")
                from database.seed_mock_data import MockDataSeeder
                
                seeder = MockDataSeeder()
                result = seeder.seed_database(clear_existing=False)
                
                if result["success"]:
                    print("✅ Database seeded successfully")
                    return True
                else:
                    print(f"❌ Database seeding failed: {result['message']}")
                    return False
            else:
                print(f"✅ Database has {user_count} users, skipping seeding")
                return True
                
    except Exception as e:
        print(f"❌ Database seeding check failed: {e}")
        return False

def start_api_server(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI server"""
    print(f"🚀 Starting API server on {host}:{port}...")
    
    try:
        import uvicorn
        
        # Configure logging
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
        
        # Start server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_config=log_config,
            access_log=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🏫 Smart Campus Access Control API - Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        return 1
    
    # Check database
    if not check_database():
        print("❌ Database check failed")
        print("💡 Make sure MySQL is running and accessible")
        return 1
    
    # Initialize database
    if not initialize_database():
        print("❌ Database initialization failed")
        return 1
    
    # Seed database if needed
    if not seed_database_if_empty():
        print("⚠️ Database seeding failed, but continuing...")
    
    print("\n🎉 Startup checks completed successfully!")
    print("📚 API Documentation will be available at: http://localhost:8000/docs")
    print("📊 Dashboard API at: http://localhost:8000/api/dashboard")
    print("🔍 Health check at: http://localhost:8000/health")
    print("\n🚀 Starting server...")
    print("=" * 50)
    
    # Start API server
    start_api_server()
    
    return 0

if __name__ == "__main__":
    exit(main())