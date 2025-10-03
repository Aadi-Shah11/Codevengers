-- Performance optimization indexes for Smart Campus Access Control
-- Run this after creating the main schema

USE campus_access_control;

-- Users table indexes
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_department ON users(department);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_email ON users(email);

-- Vehicles table indexes  
CREATE INDEX idx_vehicles_owner ON vehicles(owner_id);
CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type);
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_color ON vehicles(color);

-- Access logs table indexes (already in schema but adding composite indexes)
CREATE INDEX idx_logs_timestamp_gate ON access_logs(timestamp, gate_id);
CREATE INDEX idx_logs_user_timestamp ON access_logs(user_id, timestamp);
CREATE INDEX idx_logs_plate_timestamp ON access_logs(license_plate, timestamp);
CREATE INDEX idx_logs_granted_timestamp ON access_logs(access_granted, timestamp);
CREATE INDEX idx_logs_alert_timestamp ON access_logs(alert_triggered, timestamp);

-- Alerts table indexes
CREATE INDEX idx_alerts_type_created ON alerts(alert_type, created_at);
CREATE INDEX idx_alerts_resolved_created ON alerts(resolved, created_at);
CREATE INDEX idx_alerts_gate_created ON alerts(gate_id, created_at);

-- Full-text search indexes for better search performance
ALTER TABLE users ADD FULLTEXT(name, email);
ALTER TABLE access_logs ADD FULLTEXT(notes);
ALTER TABLE alerts ADD FULLTEXT(message);

-- Show all indexes for verification
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    INDEX_TYPE
FROM 
    INFORMATION_SCHEMA.STATISTICS 
WHERE 
    TABLE_SCHEMA = 'campus_access_control'
ORDER BY 
    TABLE_NAME, INDEX_NAME;