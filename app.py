from flask import Flask, render_template, request, jsonify, Response
import cv2
import json
import os
import numpy as np
from datetime import datetime, date
import threading
import time
import base64

from camera import CameraManager
from attendance import AttendanceManager
from db import DatabaseManager
import config

app = Flask(__name__)

# Global instances
camera = CameraManager()
attendance_manager = AttendanceManager()

# Global state for face recognition simulation
current_state = {
    'mode': 'recognition',
    'new_user_detected': False,
    'last_recognition': None,
    'registered_faces': {},  # Simple face storage
    'face_cascade': cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
}

def process_frame():
    """Continuous frame processing for face detection and recognition"""
    global current_state
    
    while True:
        try:
            if not camera.is_running():
                time.sleep(1)
                continue
            
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            
            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = current_state['face_cascade'].detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0 and current_state['mode'] == 'recognition':
                # Check if we have registered faces
                if current_state['registered_faces']:
                    # Simulate recognition by checking face position/size similarity
                    for student_id, face_data in current_state['registered_faces'].items():
                        # Simple recognition simulation
                        student_details = attendance_manager.get_student_details(student_id)
                        if student_details:
                            current_state['last_recognition'] = {
                                'student': student_details,
                                'timestamp': datetime.now().isoformat(),
                                'face_location': faces[0]
                            }
                            
                            # Try to mark attendance
                            success, message = attendance_manager.mark_student_attendance(student_id)
                            current_state['last_recognition']['attendance_result'] = {
                                'success': success,
                                'message': message
                            }
                            break
                else:
                    # New user detected
                    if not current_state['new_user_detected']:
                        current_state['new_user_detected'] = True
                        current_state['mode'] = 'registration'
                        print("New user detected - Registration required")
            
            elif len(faces) == 0:
                # No faces detected, reset recognition after delay
                if current_state['last_recognition']:
                    last_time = datetime.fromisoformat(current_state['last_recognition']['timestamp'])
                    if (datetime.now() - last_time).seconds > 3:
                        current_state['last_recognition'] = None
            
            time.sleep(0.2)  # Reduce CPU usage
            
        except Exception as e:
            print(f"Error in frame processing: {e}")
            time.sleep(1)

# Start background processing
processing_thread = threading.Thread(target=process_frame)
processing_thread.daemon = True
processing_thread.start()

@app.route('/')
def index():
    """Main student view"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route with face detection"""
    def generate():
        while True:
            frame = camera.get_frame()
            if frame is not None:
                # Detect and draw faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = current_state['face_cascade'].detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in faces:
                    if current_state['last_recognition']:
                        # Green for recognized
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        student = current_state['last_recognition']['student']
                        cv2.putText(frame, f"Student: {student['name']}", (x, y-30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        cv2.putText(frame, f"ID: {student['student_id']}", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    elif current_state['new_user_detected']:
                        # Red for new user
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, "New User - Registration Required", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    else:
                        # Blue for detected face
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                        cv2.putText(frame, "Face Detected", (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                
                # Add system status
                status_text = f"Mode: {current_state['mode'].upper()}"
                cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Encode frame
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                time.sleep(0.1)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    attendance_status = attendance_manager.get_attendance_status()
    
    return jsonify({
        'camera_running': camera.is_running(),
        'attendance_status': attendance_status,
        'current_state': current_state['mode'],
        'new_user_detected': current_state['new_user_detected'],
        'last_recognition': current_state['last_recognition'],
        'registered_users': len(current_state['registered_faces'])
    })

@app.route('/api/registration/approve', methods=['POST'])
def approve_registration():
    """Approve new user registration"""
    global current_state
    
    try:
        data = request.json
        name = data.get('name')
        student_id = data.get('student_id')
        class_name = data.get('class')
        department = data.get('department')
        roll_no = data.get('roll_no')
        
        if not all([name, student_id, class_name, department, roll_no]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Capture current frame for face storage
        frame = camera.get_frame()
        if frame is None:
            return jsonify({'success': False, 'message': 'No camera frame available'})
        
        # Save face image
        face_image_path = f"face_images/{student_id}.jpg"
        cv2.imwrite(face_image_path, frame)
        
        # Store in database (without face encoding)
        db = DatabaseManager()
        success = db.add_student(name, student_id, class_name, department, roll_no, face_image_path, "opencv_detection")
        db.close()
        
        if success:
            # Add to registered faces (simple storage)
            current_state['registered_faces'][student_id] = {
                'name': name,
                'image_path': face_image_path,
                'registered_at': datetime.now().isoformat()
            }
            
            # Reset state
            current_state['new_user_detected'] = False
            current_state['mode'] = 'recognition'
            
            return jsonify({'success': True, 'message': 'Student registered successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to register student'})
            
    except Exception as e:
        print(f"Error in registration approval: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'})

@app.route('/api/registration/reject', methods=['POST'])
def reject_registration():
    """Reject new user registration"""
    global current_state
    
    current_state['new_user_detected'] = False
    current_state['mode'] = 'recognition'
    
    return jsonify({'success': True, 'message': 'Registration rejected'})

@app.route('/api/attendance/settings', methods=['GET', 'POST'])
def attendance_settings():
    """Get or update attendance settings"""
    if request.method == 'GET':
        status = attendance_manager.get_attendance_status()
        return jsonify(status)
    
    elif request.method == 'POST':
        data = request.json
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        success, message = attendance_manager.update_attendance_window(start_time, end_time)
        return jsonify({'success': success, 'message': message})

@app.route('/api/attendance/records')
def attendance_records():
    """Get attendance records"""
    date_filter = request.args.get('date')
    if date_filter:
        try:
            datetime.strptime(date_filter, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'})
    
    records = attendance_manager.get_attendance_records(date_filter)
    
    # Convert datetime objects to strings
    for record in records:
        if 'date' in record and record['date']:
            record['date'] = record['date'].strftime('%Y-%m-%d')
        if 'time' in record and record['time']:
            record['time'] = record['time'].strftime('%H:%M:%S')
    
    return jsonify(records)

@app.route('/api/students')
def get_students():
    """Get all registered students"""
    try:
        db = DatabaseManager()
        students = db.get_approved_students()
        db.close()
        
        return jsonify(students)
    except Exception as e:
        print(f"Error fetching students: {e}")
        return jsonify([])

@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    """Start camera"""
    if camera.start():
        return jsonify({'success': True, 'message': 'Camera started'})
    else:
        return jsonify({'success': False, 'message': 'Failed to start camera'})

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    """Stop camera"""
    camera.stop()
    return jsonify({'success': True, 'message': 'Camera stopped'})

@app.route('/api/simulate_attendance/<student_id>', methods=['POST'])
def simulate_attendance(student_id):
    """Simulate attendance marking for testing"""
    success, message = attendance_manager.mark_student_attendance(student_id)
    return jsonify({'success': success, 'message': message})

if __name__ == '__main__':
    print("=" * 60)
    print("🎓 FACE RECOGNITION ATTENDANCE SYSTEM")
    print("=" * 60)
    print("🔧 Initializing system...")
    
    # Initialize database
    try:
        db = DatabaseManager()
        db.create_database()
        print("✅ Database initialized")
        
        # Load existing registered faces
        students = db.get_approved_students()
        for student in students:
            current_state['registered_faces'][student['student_id']] = {
                'name': student['name'],
                'image_path': student.get('face_image_path', ''),
                'registered_at': student.get('created_at', datetime.now()).isoformat()
            }
        print(f"✅ Loaded {len(current_state['registered_faces'])} registered students")
        
        db.close()
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
    
    # Start camera
    if camera.start():
        print("✅ Camera started successfully")
    else:
        print("⚠️  Camera failed to start - system will work without video")
    
    print("\n🌐 Starting web server...")
    print("📱 Student View: http://localhost:5000")
    print("👨‍💼 Admin Panel: http://localhost:5000/admin")
    print("=" * 60)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
    finally:
        camera.stop()
        attendance_manager.close()
        print("✅ System shutdown complete")