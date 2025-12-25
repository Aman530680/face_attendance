from flask import Flask, render_template, request, jsonify, Response
import cv2
import json
import os
from datetime import datetime, date
import threading
import time

from camera import CameraManager
from attendance import AttendanceManager
from db import DatabaseManager
import config

app = Flask(__name__)

# Global instances
camera = CameraManager()
attendance_manager = AttendanceManager()

# Global state
current_state = {
    'mode': 'recognition',
    'new_user_detected': False,
    'last_recognition': None
}

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
                # Simple face detection using OpenCV
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(frame, "Face Detected", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                time.sleep(0.1)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    attendance_status = attendance_manager.get_attendance_status()
    
    return jsonify({
        'camera_running': camera.is_running(),
        'attendance_status': attendance_status,
        'current_state': current_state['mode'],
        'new_user_detected': False,
        'last_recognition': None
    })

@app.route('/api/attendance/settings', methods=['GET', 'POST'])
def attendance_settings():
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
    date_filter = request.args.get('date')
    records = attendance_manager.get_attendance_records(date_filter)
    
    for record in records:
        if 'date' in record:
            record['date'] = record['date'].strftime('%Y-%m-%d')
        if 'time' in record:
            record['time'] = record['time'].strftime('%H:%M:%S')
    
    return jsonify(records)

if __name__ == '__main__':
    # Initialize database
    db = DatabaseManager()
    db.create_database()
    db.close()
    
    # Start camera
    camera.start()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    finally:
        camera.stop()
        attendance_manager.close()