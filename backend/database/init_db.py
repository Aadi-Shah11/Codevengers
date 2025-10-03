#!/usr/bin/env python3
"""
Database initialization script for Smart Campus Access Control
Creates database, tables, and populates with mock data
"""

import mysql.connector
from mysql.connector import Error
import sys
import os
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',  # Change this to your MySQL root password
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def create_connection():
    """Create MySQL connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            print("✅ Connected to MySQL server")
            return connection
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def execute_sql_file(connection, file_path):
    """Execute SQL commands from file"""
    try:
        cursor = connection.cursor()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_commands = file.read()
        
        # Split commands by semicolon and execute each
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip()]
        
        for command in commands:
            if command:
                cursor.execute(command)
        
        connection.commit()
        cursor.close()
        print(f"✅ Successfully executed {file_path}")
        return True
        
    except Error as e:
        print(f"❌ Error executing {file_path}: {e}")
        return False

def verify_database():
    """Verify database and tables were created successfully"""
    try:
        connection = mysql.connector.connect(
            **DB_CONFIG,
            database='campus_access_control'
        )
        cursor = connection.cursor()
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print("\n📋 Database Tables Created:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} records")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        print(f"❌ Error verifying database: {e}")
        return False

def main():
    """Main initialization function"""
    print("🚀 Initializing Smart Campus Access Control Database...")
    
    # Get current directory
    current_dir = Path(__file__).parent
    
    # SQL file paths
    schema_file = current_dir / 'schema.sql'
    seed_file = current_dir / 'seed_data.sql'
    
    # Check if SQL files exist
    if not schema_file.exists():
        print(f"❌ Schema file not found: {schema_file}")
        sys.exit(1)
    
    if not seed_file.exists():
        print(f"❌ Seed data file not found: {seed_file}")
        sys.exit(1)
    
    # Create connection
    connection = create_connection()
    if not connection:
        sys.exit(1)
    
    try:
        # Execute schema creation
        print("\n📊 Creating database schema...")
        if not execute_sql_file(connection, schema_file):
            sys.exit(1)
        
        # Execute seed data
        print("\n🌱 Inserting seed data...")
        if not execute_sql_file(connection, seed_file):
            sys.exit(1)
        
        # Execute indexes for performance
        indexes_file = current_dir / 'indexes.sql'
        if indexes_file.exists():
            print("\n⚡ Creating performance indexes...")
            execute_sql_file(connection, indexes_file)
        
        # Execute views for reporting
        views_file = current_dir / 'views.sql'
        if views_file.exists():
            print("\n👁️ Creating database views...")
            execute_sql_file(connection, views_file)
        
        # Execute stored procedures
        procedures_file = current_dir / 'procedures.sql'
        if procedures_file.exists():
            print("\n⚙️ Creating stored procedures...")
            execute_sql_file(connection, procedures_file)
        
        # Verify setup
        print("\n🔍 Verifying database setup...")
        if verify_database():
            print("\n🎉 Database initialization completed successfully!")
            print("\n📝 Next steps:")
            print("  1. Start the FastAPI backend: python main.py")
            print("  2. Run the Flutter app: flutter run")
            print("  3. Open web dashboard: web-dashboard/index.html")
        else:
            print("\n❌ Database verification failed")
            sys.exit(1)
            
    finally:
        if connection.is_connected():
            connection.close()

if __name__ == "__main__":
    main()