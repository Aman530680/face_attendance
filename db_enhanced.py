import mysql.connector
from mysql.connector import Error
import config
from datetime import datetime, date, time
import json

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
    
    def create_tables(self):
        """Create all required tables with enhanced schema"""
        tables = {
            'users': """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    user_id VARCHAR(50) UNIQUE NOT NULL,
                    role ENUM('student', 'employee') DEFAULT 'student',
                    department VARCHAR(100),
                    class_section VARCHAR(50),
                    phone VARCHAR(20),
                    email VARCHAR(100),
                    face_image_path VARCHAR(255),
                    face_encoding TEXT,
                    status ENUM('active', 'inactive') DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """,
            'attendance_records': """
                CREATE TABLE IF NOT EXISTS attendance_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(50),
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    status ENUM('Present', 'Absent') DEFAULT 'Present',
                    schedule_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_attendance (user_id, date, schedule_id)
                )
            """,
            'attendance_schedules': """
                CREATE TABLE IF NOT EXISTS attendance_schedules (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    schedule_type ENUM('fixed', 'recurring', 'custom') NOT NULL,
                    start_time TIME,
                    end_time TIME,
                    days_of_week JSON,
                    interval_minutes INT DEFAULT 60,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """,
            'system_settings': """
                CREATE TABLE IF NOT EXISTS system_settings (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    setting_key VARCHAR(100) UNIQUE NOT NULL,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """
        }
        
        try:
            cursor = self.connection.cursor()
            for table_name, query in tables.items():
                cursor.execute(query)
                print(f"Table {table_name} created successfully")
            
            # Insert default settings
            default_settings = [
                ('camera_always_on', 'true'),
                ('capture_mode', 'continuous'),
                ('default_schedule_id', '1')
            ]
            
            for key, value in default_settings:
                cursor.execute(
                    "INSERT IGNORE INTO system_settings (setting_key, setting_value) VALUES (%s, %s)",
                    (key, value)
                )
            
            # Insert default schedule
            cursor.execute("""
                INSERT IGNORE INTO attendance_schedules 
                (id, name, schedule_type, start_time, end_time, days_of_week) 
                VALUES (1, 'Daily Attendance', 'fixed', '09:00:00', '17:00:00', '["1","2","3","4","5"]')
            """)
            
            self.connection.commit()
            cursor.close()
        except Error as e:
            print(f"Error creating tables: {e}")
    
    # CRUD Operations for Users
    def create_user(self, name, user_id, role='student', department='', class_section='', 
                   phone='', email='', face_image_path='', face_encoding=''):
        """Create new user"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            query = """
                INSERT INTO users (name, user_id, role, department, class_section, 
                                 phone, email, face_image_path, face_encoding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, user_id, role, department, class_section, 
                                 phone, email, face_image_path, face_encoding))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error creating user: {e}")
            return False
    
    def get_all_users(self):
        """Read all users"""
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE status = 'active' ORDER BY created_at DESC")
            users = cursor.fetchall()
            cursor.close()
            return users
        except Error as e:
            print(f"Error fetching users: {e}")
            return []
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            return user
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
    
    def update_user(self, user_id, **kwargs):
        """Update user details"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'role', 'department', 'class_section', 'phone', 'email', 'face_image_path', 'face_encoding']:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
            
            if not set_clauses:
                return False
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = %s"
            values.append(user_id)
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating user: {e}")
            return False
    
    def delete_user(self, user_id):
        """Delete user (soft delete)"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE users SET status = 'inactive' WHERE user_id = %s", (user_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error deleting user: {e}")
            return False
    
    # CRUD Operations for Schedules
    def create_schedule(self, name, schedule_type, start_time=None, end_time=None, 
                       days_of_week=None, interval_minutes=60):
        """Create attendance schedule"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            days_json = json.dumps(days_of_week) if days_of_week else None
            
            query = """
                INSERT INTO attendance_schedules 
                (name, schedule_type, start_time, end_time, days_of_week, interval_minutes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, schedule_type, start_time, end_time, days_json, interval_minutes))
            self.connection.commit()
            schedule_id = cursor.lastrowid
            cursor.close()
            return schedule_id
        except Error as e:
            print(f"Error creating schedule: {e}")
            return None
    
    def get_all_schedules(self):
        """Get all schedules"""
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM attendance_schedules WHERE is_active = TRUE ORDER BY created_at DESC")
            schedules = cursor.fetchall()
            
            # Parse JSON days_of_week
            for schedule in schedules:
                if schedule['days_of_week']:
                    schedule['days_of_week'] = json.loads(schedule['days_of_week'])
            
            cursor.close()
            return schedules
        except Error as e:
            print(f"Error fetching schedules: {e}")
            return []
    
    def update_schedule(self, schedule_id, **kwargs):
        """Update schedule"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                if key in ['name', 'schedule_type', 'start_time', 'end_time', 'interval_minutes', 'is_active']:
                    set_clauses.append(f"{key} = %s")
                    values.append(value)
                elif key == 'days_of_week':
                    set_clauses.append("days_of_week = %s")
                    values.append(json.dumps(value) if value else None)
            
            if not set_clauses:
                return False
            
            query = f"UPDATE attendance_schedules SET {', '.join(set_clauses)} WHERE id = %s"
            values.append(schedule_id)
            
            cursor.execute(query, values)
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating schedule: {e}")
            return False
    
    def delete_schedule(self, schedule_id):
        """Delete schedule"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("UPDATE attendance_schedules SET is_active = FALSE WHERE id = %s", (schedule_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error deleting schedule: {e}")
            return False
    
    # Attendance Operations
    def mark_attendance(self, user_id, schedule_id=1):
        """Mark attendance for user"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            today = date.today()
            current_time = datetime.now().time()
            
            query = """
                INSERT INTO attendance_records (user_id, date, time, schedule_id)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE time = VALUES(time)
            """
            cursor.execute(query, (user_id, today, current_time, schedule_id))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error marking attendance: {e}")
            return False
    
    def get_attendance_records(self, date_filter=None, user_id=None):
        """Get attendance records with filters"""
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT ar.*, u.name, u.role, u.department, u.class_section,
                       s.name as schedule_name
                FROM attendance_records ar
                JOIN users u ON ar.user_id = u.user_id
                LEFT JOIN attendance_schedules s ON ar.schedule_id = s.id
                WHERE 1=1
            """
            params = []
            
            if date_filter:
                query += " AND ar.date = %s"
                params.append(date_filter)
            
            if user_id:
                query += " AND ar.user_id = %s"
                params.append(user_id)
            
            query += " ORDER BY ar.date DESC, ar.time DESC"
            
            cursor.execute(query, params)
            records = cursor.fetchall()
            cursor.close()
            return records
        except Error as e:
            print(f"Error fetching attendance records: {e}")
            return []
    
    def delete_attendance_record(self, record_id):
        """Delete attendance record"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM attendance_records WHERE id = %s", (record_id,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error deleting attendance record: {e}")
            return False
    
    # System Settings
    def get_setting(self, key):
        """Get system setting"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("SELECT setting_value FROM system_settings WHERE setting_key = %s", (key,))
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result else None
        except Error as e:
            print(f"Error getting setting: {e}")
            return None
    
    def update_setting(self, key, value):
        """Update system setting"""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO system_settings (setting_key, setting_value) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value)
            """, (key, value))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error updating setting: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")