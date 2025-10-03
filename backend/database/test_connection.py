#!/usr/bin/env python3
"""
Simple database connection test for Smart Campus Access Control
"""

import mysql.connector
from mysql.connector import Error

def test_connection():
    """Test MySQL connection and basic operations"""
    print("🔍 Testing MySQL Connection...")
    
    try:
        # Test connection without database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='password'  # Change this to your MySQL root password
        )
        
        if connection.is_connected():
            print("✅ MySQL server connection successful")
            
            cursor = connection.cursor()
            
            # Check if database exists
            cursor.execute("SHOW DATABASES LIKE 'campus_access_control'")
            db_exists = cursor.fetchone()
            
            if db_exists:
                print("✅ Database 'campus_access_control' exists")
                
                # Connect to the database
                cursor.execute("USE campus_access_control")
                
                # Check tables
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                
                if tables:
                    print("✅ Database tables found:")
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        count = cursor.fetchone()[0]
                        print(f"   - {table[0]}: {count} records")
                else:
                    print("⚠️  No tables found in database")
                    
            else:
                print("❌ Database 'campus_access_control' not found")
                print("💡 Run: python backend/database/init_db.py")
            
            cursor.close()
            connection.close()
            
    except Error as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure MySQL server is running")
        print("   2. Check username and password in the script")
        print("   3. Verify MySQL is installed and accessible")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()