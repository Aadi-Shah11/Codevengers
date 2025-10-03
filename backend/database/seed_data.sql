-- Mock data for Smart Campus Access Control System
-- Comprehensive test data for demonstration and development

USE campus_access_control;

-- Clear existing data (in dependency order)
DELETE FROM alerts;
DELETE FROM access_logs;
DELETE FROM vehicles;
DELETE FROM users;

-- Reset auto-increment counters
ALTER TABLE access_logs AUTO_INCREMENT = 1;
ALTER TABLE alerts AUTO_INCREMENT = 1;

-- Insert comprehensive user data (students, staff, faculty)
INSERT INTO users (id, name, email, role, department, status) VALUES
-- Students
('STU001', 'John Doe', 'john.doe@university.edu', 'student', 'Computer Science', 'active'),
('STU002', 'Alice Johnson', 'alice.johnson@university.edu', 'student', 'Engineering', 'active'),
('STU003', 'Bob Wilson', 'bob.wilson@university.edu', 'student', 'Mathematics', 'active'),
('STU004', 'Emma Davis', 'emma.davis@university.edu', 'student', 'Physics', 'active'),
('STU005', 'Michael Chen', 'michael.chen@university.edu', 'student', 'Computer Science', 'inactive'),
('STU006', 'Sarah Kim', 'sarah.kim@university.edu', 'student', 'Biology', 'active'),
('STU007', 'David Rodriguez', 'david.rodriguez@university.edu', 'student', 'Chemistry', 'active'),

-- Staff
('STF001', 'Jane Smith', 'jane.smith@university.edu', 'staff', 'Administration', 'active'),
('STF002', 'Michael Brown', 'michael.brown@university.edu', 'staff', 'Security', 'active'),
('STF003', 'Sarah Miller', 'sarah.miller@university.edu', 'staff', 'IT Services', 'active'),
('STF004', 'Robert Johnson', 'robert.johnson@university.edu', 'staff', 'Facilities', 'active'),
('STF005', 'Lisa Wong', 'lisa.wong@university.edu', 'staff', 'Library', 'active'),

-- Faculty
('FAC001', 'Dr. Robert Taylor', 'robert.taylor@university.edu', 'faculty', 'Computer Science', 'active'),
('FAC002', 'Prof. Lisa Anderson', 'lisa.anderson@university.edu', 'faculty', 'Engineering', 'active'),
('FAC003', 'Dr. David Martinez', 'david.martinez@university.edu', 'faculty', 'Mathematics', 'active'),
('FAC004', 'Prof. Jennifer Lee', 'jennifer.lee@university.edu', 'faculty', 'Physics', 'active'),
('FAC005', 'Dr. Thomas Wilson', 'thomas.wilson@university.edu', 'faculty', 'Biology', 'active');

-- Insert comprehensive vehicle data
INSERT INTO vehicles (license_plate, owner_id, vehicle_type, color, model, status) VALUES
-- Student vehicles
('ABC123', 'STU001', 'car', 'Blue', 'Honda Civic', 'active'),
('DEF456', 'STU002', 'motorcycle', 'Black', 'Yamaha R15', 'active'),
('JKL012', 'STU003', 'bicycle', 'Green', 'Trek Mountain', 'active'),
('PQR678', 'STU004', 'motorcycle', 'Red', 'Honda CBR', 'active'),
('STU999', 'STU005', 'car', 'White', 'Toyota Corolla', 'inactive'),
('MNP456', 'STU006', 'bicycle', 'Pink', 'Giant Escape', 'active'),
('QRS789', 'STU007', 'car', 'Black', 'Mazda 3', 'active'),

-- Staff vehicles
('XYZ789', 'STF001', 'car', 'Red', 'Toyota Camry', 'active'),
('MNO345', 'STF002', 'car', 'Silver', 'Ford Focus', 'active'),
('VWX234', 'STF003', 'car', 'Blue', 'Nissan Altima', 'active'),
('TUV123', 'STF004', 'car', 'Green', 'Subaru Outback', 'active'),
('WXY456', 'STF005', 'bicycle', 'Purple', 'Specialized Hybrid', 'active'),

-- Faculty vehicles
('GHI789', 'FAC001', 'car', 'White', 'BMW 320i', 'active'),
('YZA567', 'FAC002', 'car', 'Gray', 'Mercedes C-Class', 'active'),
('BCD890', 'FAC003', 'car', 'Navy', 'Lexus ES', 'active'),
('EFG123', 'FAC004', 'car', 'Silver', 'Audi A4', 'active'),
('HIJ456', 'FAC005', 'car', 'Black', 'Volvo XC60', 'active');

-- Insert realistic access logs (last 7 days)
INSERT INTO access_logs (timestamp, gate_id, user_id, license_plate, verification_method, access_granted, alert_triggered, notes) VALUES
-- Recent successful attempts
(NOW() - INTERVAL 1 HOUR, 'MAIN_GATE', 'STU001', 'ABC123', 'both', TRUE, FALSE, 'Successful dual verification'),
(NOW() - INTERVAL 2 HOUR, 'MAIN_GATE', 'FAC001', NULL, 'id_only', TRUE, FALSE, 'Faculty ID verification'),
(NOW() - INTERVAL 3 HOUR, 'PARKING_GATE', NULL, 'XYZ789', 'vehicle_only', TRUE, FALSE, 'Vehicle-only access'),
(NOW() - INTERVAL 4 HOUR, 'SIDE_GATE', 'STF002', 'MNO345', 'both', TRUE, FALSE, 'Staff dual verification'),

-- Yesterday's activity
(NOW() - INTERVAL 1 DAY - INTERVAL 2 HOUR, 'MAIN_GATE', 'STU002', 'DEF456', 'both', TRUE, FALSE, 'Student motorcycle access'),
(NOW() - INTERVAL 1 DAY - INTERVAL 4 HOUR, 'MAIN_GATE', 'FAC002', 'YZA567', 'both', TRUE, FALSE, 'Faculty vehicle access'),
(NOW() - INTERVAL 1 DAY - INTERVAL 6 HOUR, 'SIDE_GATE', 'STU003', NULL, 'id_only', TRUE, FALSE, 'Student ID-only access'),
(NOW() - INTERVAL 1 DAY - INTERVAL 8 HOUR, 'PARKING_GATE', NULL, 'GHI789', 'vehicle_only', TRUE, FALSE, 'Faculty vehicle parking'),

-- Failed attempts (for alerts)
(NOW() - INTERVAL 30 MINUTE, 'MAIN_GATE', 'INVALID001', NULL, 'id_only', FALSE, TRUE, 'Invalid student ID attempted'),
(NOW() - INTERVAL 45 MINUTE, 'SIDE_GATE', NULL, 'FAKE123', 'vehicle_only', FALSE, TRUE, 'Unregistered vehicle detected'),
(NOW() - INTERVAL 2 DAY, 'MAIN_GATE', 'EXPIRED999', NULL, 'id_only', FALSE, TRUE, 'Expired ID card used'),

-- Older successful attempts
(NOW() - INTERVAL 2 DAY - INTERVAL 3 HOUR, 'MAIN_GATE', 'STF001', 'XYZ789', 'both', TRUE, FALSE, 'Administration staff access'),
(NOW() - INTERVAL 3 DAY - INTERVAL 1 HOUR, 'PARKING_GATE', 'FAC003', 'BCD890', 'both', TRUE, FALSE, 'Faculty parking access'),
(NOW() - INTERVAL 3 DAY - INTERVAL 5 HOUR, 'SIDE_GATE', 'STU004', 'PQR678', 'both', TRUE, FALSE, 'Student motorcycle entry'),
(NOW() - INTERVAL 4 DAY - INTERVAL 2 HOUR, 'MAIN_GATE', 'STF003', NULL, 'id_only', TRUE, FALSE, 'IT staff ID access'),

-- Weekend activity (less frequent)
(NOW() - INTERVAL 5 DAY - INTERVAL 10 HOUR, 'MAIN_GATE', 'FAC001', 'GHI789', 'both', TRUE, FALSE, 'Weekend faculty access'),
(NOW() - INTERVAL 6 DAY - INTERVAL 14 HOUR, 'SIDE_GATE', 'STF002', NULL, 'id_only', TRUE, FALSE, 'Weekend security check'),

-- More failed attempts for testing
(NOW() - INTERVAL 3 DAY - INTERVAL 2 HOUR, 'PARKING_GATE', NULL, 'VISITOR99', 'vehicle_only', FALSE, TRUE, 'Visitor vehicle not registered'),
(NOW() - INTERVAL 4 DAY - INTERVAL 6 HOUR, 'MAIN_GATE', 'TEMP123', NULL, 'id_only', FALSE, TRUE, 'Temporary ID not in system'),
(NOW() - INTERVAL 5 DAY - INTERVAL 8 HOUR, 'SIDE_GATE', 'STU005', 'STU999', 'both', FALSE, TRUE, 'Inactive student and vehicle');

-- Insert comprehensive alert data
INSERT INTO alerts (alert_type, message, user_id, license_plate, gate_id, resolved, created_at, resolved_at) VALUES
-- Recent active alerts
('unauthorized_id', 'Unauthorized ID scan attempt - ID: INVALID001', 'INVALID001', NULL, 'MAIN_GATE', FALSE, NOW() - INTERVAL 30 MINUTE, NULL),
('unauthorized_vehicle', 'Unregistered vehicle detected - Plate: FAKE123', NULL, 'FAKE123', 'SIDE_GATE', FALSE, NOW() - INTERVAL 45 MINUTE, NULL),

-- Resolved alerts
('unauthorized_id', 'Expired ID card used - ID: EXPIRED999', 'EXPIRED999', NULL, 'MAIN_GATE', TRUE, NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 1 DAY),
('unauthorized_vehicle', 'Visitor vehicle not registered - Plate: VISITOR99', NULL, 'VISITOR99', 'PARKING_GATE', TRUE, NOW() - INTERVAL 3 DAY - INTERVAL 2 HOUR, NOW() - INTERVAL 2 DAY),
('unauthorized_id', 'Temporary ID not in system - ID: TEMP123', 'TEMP123', NULL, 'MAIN_GATE', TRUE, NOW() - INTERVAL 4 DAY - INTERVAL 6 HOUR, NOW() - INTERVAL 3 DAY),
('unauthorized_id', 'Inactive student attempted access - ID: STU005', 'STU005', 'STU999', 'SIDE_GATE', TRUE, NOW() - INTERVAL 5 DAY - INTERVAL 8 HOUR, NOW() - INTERVAL 4 DAY),

-- System error alerts
('system_error', 'Camera malfunction at main gate - OCR processing failed', NULL, NULL, 'MAIN_GATE', TRUE, NOW() - INTERVAL 6 DAY, NOW() - INTERVAL 5 DAY),
('system_error', 'Network connectivity issue at parking gate', NULL, NULL, 'PARKING_GATE', FALSE, NOW() - INTERVAL 12 HOUR, NULL),

-- Historical alerts for analytics
('unauthorized_vehicle', 'Suspicious vehicle loitering - Plate: SUSPECT1', NULL, 'SUSPECT1', 'MAIN_GATE', TRUE, NOW() - INTERVAL 7 DAY, NOW() - INTERVAL 6 DAY),
('unauthorized_id', 'Multiple failed attempts - ID: HACKER99', 'HACKER99', NULL, 'SIDE_GATE', TRUE, NOW() - INTERVAL 8 DAY, NOW() - INTERVAL 7 DAY);

-- Verify data insertion
SELECT 'Users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'Vehicles', COUNT(*) FROM vehicles
UNION ALL  
SELECT 'Access Logs', COUNT(*) FROM access_logs
UNION ALL
SELECT 'Alerts', COUNT(*) FROM alerts;