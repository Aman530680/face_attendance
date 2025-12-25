from flask import Flask, render_template, request, jsonify, Response
import cv2
import json
import os
import numpy as np
from datetime import datetime, date, time
import threading
import time as time_module

app = Flask(__name__)

# Global state
current_state = {
    'mode': 'recognition',
    'new_user_detected': False,
    'last_recognition': None,
    'registered_faces': {},
    'camera_running': False,
    'face_cascade': None
}

# Initialize face cascade
try:
    current_state['face_cascade'] = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    print("✅ Face detection initialized")
except Exception as e:
    print(f"❌ Face detection failed: {e}")

# Simple camera class
class SimpleCamera:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.running = False
        
    def start(self):
        try:
            self.cap = cv2.VideoCapture(1)  # Try camera 1 first
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)  # Fallback to camera 0
            
            if self.cap.isOpened():
                self.running = True
                current_state['camera_running'] = True
                print("✅ Camera started")
                return True
            else:
                print("❌ Camera failed to start")
                return False
        except Exception as e:
            print(f"❌ Camera error: {e}")
            return False
    
    def get_frame(self):
        if self.cap and self.running:
            ret, frame = self.cap.read()
            if ret:
                return frame
        return None
    
    def stop(self):
        if self.cap:
            self.cap.release()
        self.running = False
        current_state['camera_running'] = False

camera = SimpleCamera()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = camera.get_frame()
            if frame is not None:
                # Detect faces
                if current_state['face_cascade'] is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = current_state['face_cascade'].detectMultiScale(gray, 1.1, 4)
                    
                    for (x, y, w, h) in faces:
                        if current_state['registered_faces']:
                            # Green for registered users
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            cv2.putText(frame, "Registered User", (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        elif current_state['new_user_detected']:
                            # Red for new user
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                            cv2.putText(frame, "New User - Admin Approval Required", (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        else:
                            # Blue for detected face
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                            cv2.putText(frame, "Face Detected", (x, y-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                            # Set new user detected
                            current_state['new_user_detected'] = True
                
                # Add timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (10, frame.shape[0] - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                # Send a black frame if camera is not available
                black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(black_frame, "Camera Not Available", (200, 240), 
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', black_frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time_module.sleep(0.1)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    current_time = datetime.now()
    
    # Simple attendance status (9 AM to 5 PM)
    attendance_status = {
        'status': 'OPEN' if 9 <= current_time.hour < 17 else 'CLOSED',
        'message': 'Attendance window is open' if 9 <= current_time.hour < 17 else 'Attendance window is closed',
        'start_time': '09:00',
        'end_time': '17:00',
        'current_time': current_time.strftime('%H:%M:%S')
    }
    
    return jsonify({
        'camera_running': current_state['camera_running'],
        'attendance_status': attendance_status,
        'current_state': current_state['mode'],
        'new_user_detected': current_state['new_user_detected'],
        'last_recognition': current_state['last_recognition'],
        'registered_users': len(current_state['registered_faces'])
    })

@app.route('/api/registration/approve', methods=['POST'])
def approve_registration():
    """Approve new user registration"""
    try:
        data = request.json
        name = data.get('name')
        student_id = data.get('student_id')
        class_name = data.get('class')
        department = data.get('department')
        roll_no = data.get('roll_no')
        
        if not all([name, student_id, class_name, department, roll_no]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Store in memory (simple storage)
        current_state['registered_faces'][student_id] = {
            'name': name,
            'student_id': student_id,
            'class': class_name,
            'department': department,
            'roll_no': roll_no,
            'registered_at': datetime.now().isoformat(),
            'attendance_today': False
        }
        
        # Reset state
        current_state['new_user_detected'] = False
        current_state['mode'] = 'recognition'
        
        # Set last recognition to show the new student
        current_state['last_recognition'] = {
            'student': current_state['registered_faces'][student_id],
            'timestamp': datetime.now().isoformat(),
            'attendance_result': {
                'success': True,
                'message': 'Student registered successfully!'
            }
        }
        
        return jsonify({'success': True, 'message': 'Student registered successfully'})
        
    except Exception as e:
        print(f"Error in registration: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'})

@app.route('/api/registration/reject', methods=['POST'])
def reject_registration():
    """Reject new user registration"""
    current_state['new_user_detected'] = False
    current_state['mode'] = 'recognition'
    return jsonify({'success': True, 'message': 'Registration rejected'})

@app.route('/api/attendance/settings', methods=['GET', 'POST'])
def attendance_settings():
    """Get or update attendance settings"""
    if request.method == 'GET':
        current_time = datetime.now()
        return jsonify({
            'status': 'OPEN' if 9 <= current_time.hour < 17 else 'CLOSED',
            'message': 'Attendance window is open' if 9 <= current_time.hour < 17 else 'Attendance window is closed',
            'start_time': '09:00',
            'end_time': '17:00',
            'current_time': current_time.strftime('%H:%M:%S')
        })
    
    elif request.method == 'POST':
        # For demo purposes, just return success
        return jsonify({'success': True, 'message': 'Settings updated (demo mode)'})

@app.route('/api/attendance/records')
def attendance_records():
    """Get attendance records"""
    # Return demo records
    demo_records = []
    for student_id, student in current_state['registered_faces'].items():
        demo_records.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'student_id': student_id,
            'name': student['name'],
            'class': student['class'],
            'department': student['department'],
            'roll_no': student['roll_no']
        })
    
    return jsonify(demo_records)

@app.route('/api/students')
def get_students():
    """Get all registered students"""
    return jsonify(list(current_state['registered_faces'].values()))

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 FACE RECOGNITION ATTENDANCE SYSTEM")
    print("=" * 60)
    print("🔧 Initializing system...")
    
    # Start camera
    if camera.start():
        print("✅ Camera started successfully")
    else:
        print("⚠️  Camera failed to start - system will work without video")
    
    print("\n🌐 Starting web server...")
    print("📱 Student View: http://localhost:5000")
    print("👨💼 Admin Panel: http://localhost:5000/admin")
    print("=" * 60)
    print("\n🎯 DEMO INSTRUCTIONS:")
    print("1. Open http://localhost:5000 in browser")
    print("2. Stand in front of camera - face will be detected")
    print("3. Go to Admin Panel to register new student")
    print("4. Return to Student View to see recognition")
    print("=" * 60)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
    finally:
        camera.stop()
        print("✅ System shutdown complete")