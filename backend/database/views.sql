-- Database views for Smart Campus Access Control
-- Useful views for reporting and dashboard queries

USE campus_access_control;

-- View: Recent access attempts with user details
CREATE OR REPLACE VIEW recent_access_view AS
SELECT 
    al.id,
    al.timestamp,
    al.gate_id,
    al.user_id,
    u.name as user_name,
    u.role as user_role,
    u.department,
    al.license_plate,
    v.vehicle_type,
    v.color as vehicle_color,
    v.model as vehicle_model,
    al.verification_method,
    al.access_granted,
    al.alert_triggered,
    al.notes
FROM access_logs al
LEFT JOIN users u ON al.user_id = u.id
LEFT JOIN vehicles v ON al.license_plate = v.license_plate
ORDER BY al.timestamp DESC;

-- View: Active alerts with details
CREATE OR REPLACE VIEW active_alerts_view AS
SELECT 
    a.id,
    a.alert_type,
    a.message,
    a.user_id,
    u.name as user_name,
    a.license_plate,
    v.owner_id as vehicle_owner,
    vo.name as vehicle_owner_name,
    a.gate_id,
    a.created_at,
    TIMESTAMPDIFF(MINUTE, a.created_at, NOW()) as minutes_ago
FROM alerts a
LEFT JOIN users u ON a.user_id = u.id
LEFT JOIN vehicles v ON a.license_plate = v.license_plate
LEFT JOIN users vo ON v.owner_id = vo.id
WHERE a.resolved = FALSE
ORDER BY a.created_at DESC;

-- View: Daily access statistics
CREATE OR REPLACE VIEW daily_stats_view AS
SELECT 
    DATE(timestamp) as access_date,
    gate_id,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN access_granted = TRUE THEN 1 ELSE 0 END) as granted_count,
    SUM(CASE WHEN access_granted = FALSE THEN 1 ELSE 0 END) as denied_count,
    SUM(CASE WHEN alert_triggered = TRUE THEN 1 ELSE 0 END) as alert_count,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT license_plate) as unique_vehicles
FROM access_logs
WHERE timestamp >= CURDATE() - INTERVAL 30 DAY
GROUP BY DATE(timestamp), gate_id
ORDER BY access_date DESC, gate_id;

-- View: User access summary
CREATE OR REPLACE VIEW user_access_summary AS
SELECT 
    u.id,
    u.name,
    u.role,
    u.department,
    u.status,
    COUNT(al.id) as total_access_attempts,
    SUM(CASE WHEN al.access_granted = TRUE THEN 1 ELSE 0 END) as successful_access,
    SUM(CASE WHEN al.access_granted = FALSE THEN 1 ELSE 0 END) as failed_access,
    MAX(al.timestamp) as last_access_attempt,
    COUNT(DISTINCT al.gate_id) as gates_used
FROM users u
LEFT JOIN access_logs al ON u.id = al.user_id
GROUP BY u.id, u.name, u.role, u.department, u.status
ORDER BY total_access_attempts DESC;

-- View: Vehicle access summary
CREATE OR REPLACE VIEW vehicle_access_summary AS
SELECT 
    v.license_plate,
    v.owner_id,
    u.name as owner_name,
    v.vehicle_type,
    v.color,
    v.model,
    v.status,
    COUNT(al.id) as total_access_attempts,
    SUM(CASE WHEN al.access_granted = TRUE THEN 1 ELSE 0 END) as successful_access,
    SUM(CASE WHEN al.access_granted = FALSE THEN 1 ELSE 0 END) as failed_access,
    MAX(al.timestamp) as last_access_attempt
FROM vehicles v
LEFT JOIN users u ON v.owner_id = u.id
LEFT JOIN access_logs al ON v.license_plate = al.license_plate
GROUP BY v.license_plate, v.owner_id, u.name, v.vehicle_type, v.color, v.model, v.status
ORDER BY total_access_attempts DESC;

-- View: Hourly access patterns (for analytics)
CREATE OR REPLACE VIEW hourly_access_pattern AS
SELECT 
    HOUR(timestamp) as access_hour,
    COUNT(*) as total_attempts,
    SUM(CASE WHEN access_granted = TRUE THEN 1 ELSE 0 END) as granted_count,
    AVG(CASE WHEN access_granted = TRUE THEN 1.0 ELSE 0.0 END) * 100 as success_rate
FROM access_logs
WHERE timestamp >= CURDATE() - INTERVAL 7 DAY
GROUP BY HOUR(timestamp)
ORDER BY access_hour;

-- Show all views created
SELECT 
    TABLE_NAME as view_name,
    TABLE_COMMENT as description
FROM 
    INFORMATION_SCHEMA.TABLES 
WHERE 
    TABLE_SCHEMA = 'campus_access_control' 
    AND TABLE_TYPE = 'VIEW'
ORDER BY 
    TABLE_NAME;