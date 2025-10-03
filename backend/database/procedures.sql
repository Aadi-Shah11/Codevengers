-- Stored procedures for Smart Campus Access Control
-- Common database operations for better performance

USE campus_access_control;

DELIMITER //

-- Procedure: Log access attempt
CREATE PROCEDURE LogAccessAttempt(
    IN p_gate_id VARCHAR(10),
    IN p_user_id VARCHAR(20),
    IN p_license_plate VARCHAR(20),
    IN p_verification_method ENUM('id_only', 'vehicle_only', 'both'),
    IN p_access_granted BOOLEAN,
    IN p_notes TEXT
)
BEGIN
    DECLARE v_alert_triggered BOOLEAN DEFAULT FALSE;
    
    -- Determine if alert should be triggered
    IF p_access_granted = FALSE THEN
        SET v_alert_triggered = TRUE;
    END IF;
    
    -- Insert access log
    INSERT INTO access_logs (
        gate_id, user_id, license_plate, verification_method, 
        access_granted, alert_triggered, notes
    ) VALUES (
        p_gate_id, p_user_id, p_license_plate, p_verification_method,
        p_access_granted, v_alert_triggered, p_notes
    );
    
    -- Create alert if access denied
    IF v_alert_triggered = TRUE THEN
        CALL CreateSecurityAlert(p_user_id, p_license_plate, p_gate_id);
    END IF;
    
    -- Return the log ID
    SELECT LAST_INSERT_ID() as log_id;
END //

-- Procedure: Create security alert
CREATE PROCEDURE CreateSecurityAlert(
    IN p_user_id VARCHAR(20),
    IN p_license_plate VARCHAR(20),
    IN p_gate_id VARCHAR(10)
)
BEGIN
    DECLARE v_alert_type ENUM('unauthorized_id', 'unauthorized_vehicle', 'system_error');
    DECLARE v_message TEXT;
    
    -- Determine alert type and message
    IF p_user_id IS NOT NULL AND p_license_plate IS NOT NULL THEN
        SET v_alert_type = 'unauthorized_id';
        SET v_message = CONCAT('Unauthorized access attempt - ID: ', p_user_id, ', Vehicle: ', p_license_plate);
    ELSEIF p_user_id IS NOT NULL THEN
        SET v_alert_type = 'unauthorized_id';
        SET v_message = CONCAT('Unauthorized ID scan attempt - ID: ', p_user_id);
    ELSEIF p_license_plate IS NOT NULL THEN
        SET v_alert_type = 'unauthorized_vehicle';
        SET v_message = CONCAT('Unregistered vehicle detected - Plate: ', p_license_plate);
    ELSE
        SET v_alert_type = 'system_error';
        SET v_message = 'Unknown access attempt detected';
    END IF;
    
    -- Insert alert
    INSERT INTO alerts (alert_type, message, user_id, license_plate, gate_id)
    VALUES (v_alert_type, v_message, p_user_id, p_license_plate, p_gate_id);
    
    SELECT LAST_INSERT_ID() as alert_id;
END //

-- Procedure: Verify user ID
CREATE PROCEDURE VerifyUserID(
    IN p_user_id VARCHAR(20),
    OUT p_is_valid BOOLEAN,
    OUT p_user_name VARCHAR(100),
    OUT p_user_role ENUM('student', 'staff', 'faculty'),
    OUT p_user_status ENUM('active', 'inactive')
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    
    -- Check if user exists and is active
    SELECT COUNT(*), name, role, status
    INTO v_count, p_user_name, p_user_role, p_user_status
    FROM users 
    WHERE id = p_user_id AND status = 'active'
    LIMIT 1;
    
    -- Set validity based on count
    IF v_count > 0 THEN
        SET p_is_valid = TRUE;
    ELSE
        SET p_is_valid = FALSE;
        SET p_user_name = NULL;
        SET p_user_role = NULL;
        SET p_user_status = NULL;
    END IF;
END //

-- Procedure: Verify vehicle
CREATE PROCEDURE VerifyVehicle(
    IN p_license_plate VARCHAR(20),
    OUT p_is_valid BOOLEAN,
    OUT p_owner_id VARCHAR(20),
    OUT p_owner_name VARCHAR(100),
    OUT p_vehicle_type ENUM('car', 'motorcycle', 'bicycle')
)
BEGIN
    DECLARE v_count INT DEFAULT 0;
    
    -- Check if vehicle exists and is active
    SELECT COUNT(*), v.owner_id, u.name, v.vehicle_type
    INTO v_count, p_owner_id, p_owner_name, p_vehicle_type
    FROM vehicles v
    LEFT JOIN users u ON v.owner_id = u.id
    WHERE v.license_plate = p_license_plate AND v.status = 'active'
    LIMIT 1;
    
    -- Set validity based on count
    IF v_count > 0 THEN
        SET p_is_valid = TRUE;
    ELSE
        SET p_is_valid = FALSE;
        SET p_owner_id = NULL;
        SET p_owner_name = NULL;
        SET p_vehicle_type = NULL;
    END IF;
END //

-- Procedure: Get access statistics
CREATE PROCEDURE GetAccessStatistics(
    IN p_date_from DATE,
    IN p_date_to DATE,
    IN p_gate_id VARCHAR(10)
)
BEGIN
    SELECT 
        COUNT(*) as total_attempts,
        SUM(CASE WHEN access_granted = TRUE THEN 1 ELSE 0 END) as granted_count,
        SUM(CASE WHEN access_granted = FALSE THEN 1 ELSE 0 END) as denied_count,
        SUM(CASE WHEN alert_triggered = TRUE THEN 1 ELSE 0 END) as alert_count,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT license_plate) as unique_vehicles,
        AVG(CASE WHEN access_granted = TRUE THEN 1.0 ELSE 0.0 END) * 100 as success_rate
    FROM access_logs
    WHERE DATE(timestamp) BETWEEN p_date_from AND p_date_to
    AND (p_gate_id IS NULL OR gate_id = p_gate_id);
END //

-- Procedure: Clean old logs (for maintenance)
CREATE PROCEDURE CleanOldLogs(
    IN p_days_to_keep INT
)
BEGIN
    DECLARE v_cutoff_date DATE;
    DECLARE v_deleted_count INT;
    
    SET v_cutoff_date = CURDATE() - INTERVAL p_days_to_keep DAY;
    
    -- Delete old access logs
    DELETE FROM access_logs 
    WHERE timestamp < v_cutoff_date;
    
    SET v_deleted_count = ROW_COUNT();
    
    -- Delete resolved alerts older than cutoff
    DELETE FROM alerts 
    WHERE resolved = TRUE AND created_at < v_cutoff_date;
    
    SELECT 
        v_deleted_count as logs_deleted,
        ROW_COUNT() as alerts_deleted,
        v_cutoff_date as cutoff_date;
END //

DELIMITER ;

-- Show all procedures created
SELECT 
    ROUTINE_NAME as procedure_name,
    ROUTINE_TYPE,
    CREATED,
    ROUTINE_COMMENT as description
FROM 
    INFORMATION_SCHEMA.ROUTINES 
WHERE 
    ROUTINE_SCHEMA = 'campus_access_control'
ORDER BY 
    ROUTINE_NAME;