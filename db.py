import mysql.connector
from mysql.connector import Error
import config
from datetime import datetime, date

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        try:
            if self.connection and self.connection.is_connected():
                return
            self.connection = mysql.connector.connect(**config.DB_CONFIG)
            if self.connection.is_connected():
                print("Connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None
    
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            temp_config = config.DB_CONFIG.copy()
            temp_config.pop('database')
            temp_connection = mysql.connector.connect(**temp_config)
            cursor = temp_connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_CONFIG['database']}")
            cursor.close()
            temp_connection.close()
        except Error as e:
            print(f"Error creating database: {e}")
    
    def create_tables(self):
        """Create all required tables"""
        tables = {
            'students': """
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'attendance': """
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(50),
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    status ENUM('Present') DEFAULT 'Present',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    UNIQUE KEY unique_attendance (student_id, date)
                )
            """,
            'attendance_settings': """
                CREATE TABLE IF NOT EXISTS attendance_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """
        }
        
        try:
            cursor = self.connection.cursor()
            for table_name, query in tables.items():
                cursor.execute(query)
                print(f"Table {table_name} created successfully")
            
            # Insert default attendance settings if not exists
            cursor.execute("SELECT COUNT(*) FROM attendance_settings")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO attendance_settings (start_time, end_time) VALUES (%s, %s)",
                    (config.DEFAULT_START_TIME, config.DEFAULT_END_TIME)
                )
            
            self.connection.commit()
            cursor.close()
        except Error as e:
            print(f"Error creating tables: {e}")
    
    def add_student(self, name, student_id, class_name, department, roll_no, face_image_path, face_encoding):
        """Add new student to database"""
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO students (name, student_id, class, department, roll_no, face_image_path, face_encoding, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'approved')
            """
            cursor.execute(query, (name, student_id, class_name, department, roll_no, face_image_path, face_encoding))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error adding student: {e}")
            return False
    
    def get_approved_students(self):
        """Get all approved students with face encodings"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM students WHERE status = 'approved' AND face_encoding IS NOT NULL")
            students = cursor.fetchall()
            cursor.close()
            return students
        except Error as e:
            print(f"Error fetching students: {e}")
            return []
    
    def get_student_by_id(self, student_id):
        """Get student by student_id"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            cursor.close()
            return student
        except Error as e:
            print(f"Error fetching student: {e}")
            return None
    
    def mark_attendance(self, student_id):
        """Mark attendance for student"""
        try:
            cursor = self.connection.cursor()
            today = date.today()
            current_time = datetime.now().time()
            
            query = """
                INSERT INTO attendance (student_id, date, time)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE time = VALUES(time)
            """
            cursor.execute(query, (student_id, today, current_time))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def check_attendance_today(self, student_id):
        """Check if student already marked attendance today"""
        try:
            cursor = self.connection.cursor()
            today = date.today()
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE student_id = %s AND date = %s", (student_id, today))
            count = cursor.fetchone()[0]
            cursor.close()
            return count > 0
        except Error as e:
            print(f"Error checking attendance: {e}")
            return False
    
    def get_attendance_settings(self):
        """Get current attendance time settings"""
        try:
            self.connect()  # Ensure connection
            if not self.connection:
                return None
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM attendance_settings ORDER BY id DESC LIMIT 1")
            settings = cursor.fetchone()
            cursor.close()
            return settings
        except Error as e:
            print(f"Error fetching attendance settings: {e}")
            return None
    
    def update_attendance_settings(self, start_time, end_time):
        """Update attendance time settings"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("UPDATE attendance_settings SET start_time = %s, end_time = %s", (start_time, end_time))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating attendance settings: {e}")
            return False
    
    def get_attendance_records(self, date_filter=None):
        """Get attendance records with student details"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if date_filter:
                query = """
                    SELECT a.*, s.name, s.class, s.department, s.roll_no
                    FROM attendance a
                    JOIN students s ON a.student_id = s.student_id
                    WHERE a.date = %s
                    ORDER BY a.time DESC
                """
                cursor.execute(query, (date_filter,))
            else:
                query = """
                    SELECT a.*, s.name, s.class, s.department, s.roll_no
                    FROM attendance a
                    JOIN students s ON a.student_id = s.student_id
                    ORDER BY a.date DESC, a.time DESC
                """
                cursor.execute(query)
            
            records = cursor.fetchall()
            cursor.close()
            return records
        except Error as e:
            print(f"Error fetching attendance records: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")