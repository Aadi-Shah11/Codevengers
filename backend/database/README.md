# Smart Campus Access Control - Database Documentation

## Overview

The database layer for the Smart Campus Access Control system uses MySQL 8.0+ with a well-structured schema designed for performance, security, and scalability.

## Database Schema

### Core Tables

#### 1. Users Table
Stores information about students, staff, and faculty members.

```sql
CREATE TABLE users (
    id VARCHAR(20) PRIMARY KEY,           -- Unique identifier (e.g., STU001, STF001)
    name VARCHAR(100) NOT NULL,           -- Full name
    email VARCHAR(100),                   -- Contact email
    role ENUM('student', 'staff', 'faculty'), -- User role
    department VARCHAR(50),               -- Department/division
    status ENUM('active', 'inactive'),    -- Account status
    created_at TIMESTAMP,                 -- Creation timestamp
    updated_at TIMESTAMP                  -- Last update timestamp
);
```

#### 2. Vehicles Table
Stores registered vehicle information linked to users.

```sql
CREATE TABLE vehicles (
    license_plate VARCHAR(20) PRIMARY KEY, -- License plate number
    owner_id VARCHAR(20),                  -- Foreign key to users.id
    vehicle_type ENUM('car', 'motorcycle', 'bicycle'), -- Vehicle type
    color VARCHAR(30),                     -- Vehicle color
    model VARCHAR(50),                     -- Vehicle model
    status ENUM('active', 'inactive'),     -- Registration status
    registered_at TIMESTAMP,              -- Registration timestamp
    updated_at TIMESTAMP,                  -- Last update timestamp
    FOREIGN KEY (owner_id) REFERENCES users(id)
);
```

#### 3. Access Logs Table
Comprehensive audit trail of all access attempts.

```sql
CREATE TABLE access_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,    -- Unique log entry ID
    timestamp TIMESTAMP,                  -- Access attempt time
    gate_id VARCHAR(10),                  -- Gate identifier
    user_id VARCHAR(20),                  -- User ID (if available)
    license_plate VARCHAR(20),            -- License plate (if available)
    verification_method ENUM('id_only', 'vehicle_only', 'both'), -- Method used
    access_granted BOOLEAN,               -- Access decision
    alert_triggered BOOLEAN,              -- Security alert flag
    notes TEXT,                          -- Additional notes
    created_at TIMESTAMP,                -- Log creation time
    -- Indexes for performance
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id),
    INDEX idx_license_plate (license_plate)
);
```

#### 4. Alerts Table
Security alerts and notifications for authorities.

```sql
CREATE TABLE alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,    -- Unique alert ID
    alert_type ENUM('unauthorized_id', 'unauthorized_vehicle', 'system_error'),
    message TEXT NOT NULL,                -- Alert message
    user_id VARCHAR(20),                  -- Related user ID
    license_plate VARCHAR(20),            -- Related license plate
    gate_id VARCHAR(10),                  -- Gate where alert occurred
    resolved BOOLEAN DEFAULT FALSE,       -- Resolution status
    created_at TIMESTAMP,                -- Alert creation time
    resolved_at TIMESTAMP NULL,          -- Resolution timestamp
    -- Indexes for performance
    INDEX idx_created_at (created_at),
    INDEX idx_resolved (resolved)
);
```

## Database Files

### Core Files
- **`schema.sql`** - Main database schema with table definitions
- **`seed_data.sql`** - Mock data for testing (10 users, 10 vehicles)
- **`indexes.sql`** - Performance optimization indexes
- **`views.sql`** - Useful database views for reporting
- **`procedures.sql`** - Stored procedures for common operations

### Management Scripts
- **`init_db.py`** - Automated database initialization
- **`manage_db.py`** - Database management utility
- **`test_connection.py`** - Connection testing script
- **`seed_mock_data.py`** - Comprehensive mock data seeding
- **`validate_data.py`** - Data integrity validation
- **`data_manager.py`** - All-in-one data management utility

## Setup Instructions

### 1. Prerequisites
```bash
# Install MySQL 8.0+
brew install mysql  # macOS
# or
sudo apt-get install mysql-server  # Ubuntu

# Start MySQL service
brew services start mysql  # macOS
# or
sudo systemctl start mysql  # Ubuntu
```

### 2. Database Initialization

#### Option A: Full Automated Setup (Recommended)
```bash
cd backend
python database/data_manager.py full-setup
```

#### Option B: Step-by-step Setup
```bash
cd backend
python database/init_db.py
python database/seed_mock_data.py
python database/validate_data.py
```

#### Option B: Manual Setup
```bash
# Create database and tables
mysql -u root -p < database/schema.sql

# Insert mock data
mysql -u root -p < database/seed_data.sql

# Add performance indexes
mysql -u root -p < database/indexes.sql

# Create views and procedures
mysql -u root -p < database/views.sql
mysql -u root -p < database/procedures.sql
```

### 3. Verification
```bash
# Test connection
python database/test_connection.py

# Check database status
python database/manage_db.py status
```

## Database Management

### Using the Management Utility

```bash
# Show database status
python database/manage_db.py status

# View recent access logs
python database/manage_db.py logs --limit 20

# Show active alerts
python database/manage_db.py alerts

# Get access statistics
python database/manage_db.py stats --days 7

# Test user verification
python database/manage_db.py test-user --user-id STU001

# Test vehicle verification
python database/manage_db.py test-vehicle --license-plate ABC123

# Simulate access attempt
python database/manage_db.py simulate --user-id STU001 --license-plate ABC123

# Clean up old data
python database/manage_db.py cleanup --days 30
```

## Database Views

### 1. Recent Access View
Combines access logs with user and vehicle details.
```sql
SELECT * FROM recent_access_view LIMIT 10;
```

### 2. Active Alerts View
Shows unresolved security alerts with context.
```sql
SELECT * FROM active_alerts_view;
```

### 3. Daily Statistics View
Access statistics grouped by date and gate.
```sql
SELECT * FROM daily_stats_view WHERE access_date >= CURDATE() - INTERVAL 7 DAY;
```

### 4. User Access Summary
Per-user access statistics and patterns.
```sql
SELECT * FROM user_access_summary ORDER BY total_access_attempts DESC;
```

## Stored Procedures

### 1. Log Access Attempt
```sql
CALL LogAccessAttempt('MAIN_GATE', 'STU001', 'ABC123', 'both', TRUE, 'Test access');
```

### 2. Verify User ID
```sql
CALL VerifyUserID('STU001', @is_valid, @name, @role, @status);
SELECT @is_valid, @name, @role, @status;
```

### 3. Verify Vehicle
```sql
CALL VerifyVehicle('ABC123', @is_valid, @owner_id, @owner_name, @vehicle_type);
SELECT @is_valid, @owner_id, @owner_name, @vehicle_type;
```

### 4. Get Statistics
```sql
CALL GetAccessStatistics('2025-01-01', '2025-01-31', 'MAIN_GATE');
```

## Performance Optimization

### Indexes
- **Primary Keys**: Automatic unique indexes on all primary keys
- **Foreign Keys**: Indexes on all foreign key columns
- **Timestamp Indexes**: Optimized for time-based queries
- **Composite Indexes**: Multi-column indexes for common query patterns
- **Full-text Indexes**: For search functionality on text fields

### Query Optimization Tips
1. Use prepared statements for repeated queries
2. Leverage database views for complex joins
3. Use stored procedures for multi-step operations
4. Implement connection pooling in application layer
5. Regular maintenance with `ANALYZE TABLE` and `OPTIMIZE TABLE`

## Security Considerations

### Access Control
- Use dedicated database user with minimal privileges
- Implement connection encryption (SSL/TLS)
- Regular password rotation for database accounts
- Network-level access restrictions

### Data Protection
- Sensitive data encryption at rest
- Audit logging for all database operations
- Regular security updates and patches
- Backup encryption and secure storage

## Backup and Recovery

### Backup Strategy
```bash
# Full database backup
mysqldump -u root -p campus_access_control > backup_$(date +%Y%m%d).sql

# Table-specific backup
mysqldump -u root -p campus_access_control access_logs > logs_backup.sql

# Automated backup script
0 2 * * * /usr/bin/mysqldump -u backup_user -p campus_access_control > /backups/daily_$(date +\%Y\%m\%d).sql
```

### Recovery
```bash
# Restore full database
mysql -u root -p campus_access_control < backup_20250104.sql

# Restore specific table
mysql -u root -p campus_access_control < logs_backup.sql
```

## Monitoring and Maintenance

### Performance Monitoring
```sql
-- Check table sizes
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'campus_access_control';

-- Check index usage
SELECT 
    table_name,
    index_name,
    cardinality
FROM information_schema.statistics 
WHERE table_schema = 'campus_access_control';
```

### Regular Maintenance
```sql
-- Analyze tables for optimization
ANALYZE TABLE users, vehicles, access_logs, alerts;

-- Optimize tables
OPTIMIZE TABLE access_logs;

-- Check table integrity
CHECK TABLE users, vehicles, access_logs, alerts;
```

## Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check MySQL service status
brew services list | grep mysql  # macOS
systemctl status mysql           # Linux

# Test connection
mysql -u root -p -e "SELECT 1"
```

#### Performance Issues
```sql
-- Check slow queries
SHOW PROCESSLIST;

-- Check table locks
SHOW OPEN TABLES WHERE In_use > 0;

-- Analyze query performance
EXPLAIN SELECT * FROM access_logs WHERE timestamp > NOW() - INTERVAL 1 DAY;
```

#### Data Integrity Issues
```sql
-- Check foreign key constraints
SELECT * FROM information_schema.KEY_COLUMN_USAGE 
WHERE REFERENCED_TABLE_SCHEMA = 'campus_access_control';

-- Verify data consistency
SELECT COUNT(*) FROM vehicles v 
LEFT JOIN users u ON v.owner_id = u.id 
WHERE u.id IS NULL;
```

## Development Guidelines

### Naming Conventions
- **Tables**: Lowercase with underscores (e.g., `access_logs`)
- **Columns**: Lowercase with underscores (e.g., `user_id`)
- **Indexes**: Prefix with `idx_` (e.g., `idx_timestamp`)
- **Foreign Keys**: Format as `fk_table_column`

### Data Types
- **IDs**: VARCHAR(20) for human-readable IDs
- **Timestamps**: TIMESTAMP with automatic updates
- **Status Fields**: ENUM for controlled values
- **Text Fields**: TEXT for variable-length content

### Best Practices
1. Always use transactions for multi-table operations
2. Implement proper error handling in application code
3. Use parameterized queries to prevent SQL injection
4. Regular database maintenance and monitoring
5. Document all schema changes and migrations

## API Integration

The database is designed to work seamlessly with the FastAPI backend through SQLAlchemy ORM. Key integration points:

- **Models**: SQLAlchemy models in `backend/models/`
- **Repositories**: Data access layer in `backend/repositories/`
- **Services**: Business logic in `backend/services/`
- **Connection**: Database session management in `backend/database/connection.py`

## Testing

### Test Data
The system includes comprehensive test data:
- 10 sample users across different roles
- 10 sample vehicles of various types
- Sample access logs and alerts
- Realistic data relationships

### Testing Commands
```bash
# Run all database tests
python -m pytest backend/tests/test_database.py

# Test specific functionality
python database/manage_db.py test-user --user-id STU001
python database/manage_db.py simulate --user-id STU001 --gate-id MAIN_GATE

# Data management commands
python database/data_manager.py status
python database/data_manager.py seed
python database/data_manager.py validate
python database/data_manager.py maintenance
```

This database design provides a solid foundation for the Smart Campus Access Control system with excellent performance, security, and maintainability characteristics.