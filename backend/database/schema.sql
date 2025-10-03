-- Smart Campus Access Control Database Schema
-- MySQL database initialization script

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS campus_access_control 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE campus_access_control;

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS access_logs;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS users;

-- Users table for students, staff, and faculty
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    role ENUM('student', 'staff', 'faculty') NOT NULL,
    department VARCHAR(50),
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Vehicles table for registered vehicles
CREATE TABLE IF NOT EXISTS vehicles (
    license_plate VARCHAR(20) PRIMARY KEY,
    owner_id VARCHAR(20),
    vehicle_type ENUM('car', 'motorcycle', 'bicycle') NOT NULL,
    color VARCHAR(30),
    model VARCHAR(50),
    status ENUM('active', 'inactive') DEFAULT 'active',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Access logs table for audit trail
CREATE TABLE IF NOT EXISTS access_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gate_id VARCHAR(10) DEFAULT 'MAIN_GATE',
    user_id VARCHAR(20),
    license_plate VARCHAR(20),
    verification_method ENUM('id_only', 'vehicle_only', 'both') NOT NULL,
    access_granted BOOLEAN NOT NULL,
    alert_triggered BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id),
    INDEX idx_license_plate (license_plate),
    INDEX idx_access_granted (access_granted),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Alerts table for security notifications
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    alert_type ENUM('unauthorized_id', 'unauthorized_vehicle', 'system_error') NOT NULL,
    message TEXT NOT NULL,
    user_id VARCHAR(20),
    license_plate VARCHAR(20),
    gate_id VARCHAR(10) DEFAULT 'MAIN_GATE',
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_created_at (created_at),
    INDEX idx_resolved (resolved),
    INDEX idx_alert_type (alert_type)
);