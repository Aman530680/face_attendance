-- Face Recognition Attendance System Database Setup
-- Run this script in MySQL to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS face_attendance_db;
USE face_attendance_db;

-- Create students table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    class VARCHAR(50) NOT NULL,
    department VARCHAR(100) NOT NULL,
    roll_no VARCHAR(50) NOT NULL,
    face_image_path VARCHAR(255),
    face_encoding TEXT,
    status ENUM('pending', 'approved') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_student_id (student_id),
    INDEX idx_status (status)
);

-- Create attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50),
    date DATE NOT NULL,
    time TIME NOT NULL,
    status ENUM('Present') DEFAULT 'Present',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (student_id, date),
    INDEX idx_date (date),
    INDEX idx_student_date (student_id, date)
);

-- Create attendance_settings table
CREATE TABLE IF NOT EXISTS attendance_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default attendance settings
INSERT INTO attendance_settings (start_time, end_time) 
VALUES ('09:00:00', '17:00:00')
ON DUPLICATE KEY UPDATE start_time = start_time;

-- Display table information
SHOW TABLES;
DESCRIBE students;
DESCRIBE attendance;
DESCRIBE attendance_settings;