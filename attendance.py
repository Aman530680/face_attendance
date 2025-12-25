from datetime import datetime, time
from db import DatabaseManager

class AttendanceManager:
    def __init__(self):
        self.db = DatabaseManager()
    
    def is_attendance_time(self):
        """Check if current time is within attendance window"""
        try:
            settings = self.db.get_attendance_settings()
            if not settings:
                return False, "Attendance settings not configured"
            
            current_time = datetime.now().time()
            start_time = settings['start_time']
            end_time = settings['end_time']
            
            # Convert to datetime.time objects if they're not already
            if isinstance(start_time, str):
                start_time = datetime.strptime(start_time, '%H:%M').time()
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M').time()
            
            if start_time <= current_time <= end_time:
                return True, "Attendance window is open"
            else:
                return False, f"Attendance closed. Window: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
                
        except Exception as e:
            print(f"Error checking attendance time: {e}")
            return False, "Error checking attendance time"
    
    def mark_student_attendance(self, student_id):
        """Mark attendance for a student with all validations"""
        try:
            # Check if attendance window is open
            is_open, message = self.is_attendance_time()
            if not is_open:
                return False, message
            
            # Check if student exists and is approved
            student = self.db.get_student_by_id(student_id)
            if not student:
                return False, "Student not found"
            
            if student['status'] != 'approved':
                return False, "Student not approved"
            
            # Check if already marked attendance today
            if self.db.check_attendance_today(student_id):
                return False, "Attendance already marked today"
            
            # Mark attendance
            if self.db.mark_attendance(student_id):
                return True, "Attendance marked successfully"
            else:
                return False, "Failed to mark attendance"
                
        except Exception as e:
            print(f"Error marking attendance: {e}")
            return False, "Error marking attendance"
    
    def get_student_details(self, student_id):
        """Get complete student details"""
        try:
            student = self.db.get_student_by_id(student_id)
            if student:
                # Check today's attendance
                attendance_marked = self.db.check_attendance_today(student_id)
                student['attendance_today'] = attendance_marked
                return student
            return None
        except Exception as e:
            print(f"Error getting student details: {e}")
            return None
    
    def get_attendance_status(self):
        """Get current attendance window status"""
        try:
            settings = self.db.get_attendance_settings()
            if not settings:
                return {
                    'status': 'CLOSED',
                    'message': 'Attendance settings not configured',
                    'start_time': None,
                    'end_time': None
                }
            
            is_open, message = self.is_attendance_time()
            
            return {
                'status': 'OPEN' if is_open else 'CLOSED',
                'message': message,
                'start_time': settings['start_time'],
                'end_time': settings['end_time'],
                'current_time': datetime.now().strftime('%H:%M:%S')
            }
            
        except Exception as e:
            print(f"Error getting attendance status: {e}")
            return {
                'status': 'ERROR',
                'message': 'Error checking attendance status',
                'start_time': None,
                'end_time': None
            }
    
    def update_attendance_window(self, start_time, end_time):
        """Update attendance time window"""
        try:
            # Validate time format
            datetime.strptime(start_time, '%H:%M')
            datetime.strptime(end_time, '%H:%M')
            
            if self.db.update_attendance_settings(start_time, end_time):
                return True, "Attendance window updated successfully"
            else:
                return False, "Failed to update attendance window"
                
        except ValueError:
            return False, "Invalid time format. Use HH:MM format"
        except Exception as e:
            print(f"Error updating attendance window: {e}")
            return False, "Error updating attendance window"
    
    def get_attendance_records(self, date_filter=None):
        """Get attendance records with filtering"""
        try:
            return self.db.get_attendance_records(date_filter)
        except Exception as e:
            print(f"Error getting attendance records: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        self.db.close()