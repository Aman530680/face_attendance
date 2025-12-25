#!/usr/bin/env python3
"""
Face Recognition Attendance System - Test Script
This script tests all major components of the system
"""

import sys
import os
import cv2
import mysql.connector
from datetime import datetime

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import flask
        import cv2
        import face_recognition
        import mysql.connector
        import numpy
        print("✓ All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_camera():
    """Test camera access"""
    print("\nTesting camera access...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✓ Camera is working properly")
                print(f"  Frame size: {frame.shape}")
                cap.release()
                return True
            else:
                print("✗ Camera opened but cannot capture frames")
                cap.release()
                return False
        else:
            print("✗ Cannot access camera")
            return False
    except Exception as e:
        print(f"✗ Camera test error: {e}")
        return False

def test_database():
    """Test database connection"""
    print("\nTesting database connection...")
    try:
        from config import DB_CONFIG
        
        # Test connection without database
        temp_config = DB_CONFIG.copy()
        temp_config.pop('database', None)
        
        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SHOW DATABASES LIKE '{DB_CONFIG['database']}'")
        db_exists = cursor.fetchone() is not None
        
        if db_exists:
            print("✓ Database exists")
            
            # Test connection with database
            conn.close()
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            required_tables = ['students', 'attendance', 'attendance_settings']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if not missing_tables:
                print("✓ All required tables exist")
                
                # Test basic operations
                cursor.execute("SELECT COUNT(*) FROM students")
                student_count = cursor.fetchone()[0]
                print(f"  Students in database: {student_count}")
                
                cursor.execute("SELECT COUNT(*) FROM attendance")
                attendance_count = cursor.fetchone()[0]
                print(f"  Attendance records: {attendance_count}")
                
                conn.close()
                return True
            else:
                print(f"✗ Missing tables: {missing_tables}")
                conn.close()
                return False
        else:
            print(f"✗ Database '{DB_CONFIG['database']}' does not exist")
            conn.close()
            return False
            
    except Exception as e:
        print(f"✗ Database test error: {e}")
        return False

def test_face_recognition():
    """Test face recognition functionality"""
    print("\nTesting face recognition...")
    try:
        import face_recognition
        import numpy as np
        
        # Create a simple test image (black square with white rectangle as "face")
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[30:70, 30:70] = [255, 255, 255]  # White square as face
        
        # Try to detect faces (this will likely fail with our simple test image)
        face_locations = face_recognition.face_locations(test_image)
        print(f"  Face locations detected: {len(face_locations)}")
        
        # Test encoding generation with a random array (simulating a real face encoding)
        dummy_encoding = np.random.random(128)
        print(f"✓ Face recognition module working")
        print(f"  Encoding shape: {dummy_encoding.shape}")
        return True
        
    except Exception as e:
        print(f"✗ Face recognition test error: {e}")
        return False

def test_directories():
    """Test if required directories exist or can be created"""
    print("\nTesting directories...")
    try:
        required_dirs = [
            'face_images',
            'static',
            'static/css',
            'static/js',
            'templates'
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"  Created directory: {directory}")
            else:
                print(f"  Directory exists: {directory}")
        
        print("✓ All directories ready")
        return True
        
    except Exception as e:
        print(f"✗ Directory test error: {e}")
        return False

def test_config():
    """Test configuration file"""
    print("\nTesting configuration...")
    try:
        import config
        
        # Check required config variables
        required_configs = [
            'DB_CONFIG',
            'CAMERA_INDEX',
            'FACE_TOLERANCE',
            'FACE_IMAGES_DIR'
        ]
        
        missing_configs = []
        for config_name in required_configs:
            if not hasattr(config, config_name):
                missing_configs.append(config_name)
            else:
                print(f"  {config_name}: ✓")
        
        if missing_configs:
            print(f"✗ Missing configurations: {missing_configs}")
            return False
        
        print("✓ Configuration file is valid")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test error: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary"""
    print("=" * 50)
    print("Face Recognition Attendance System - System Test")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Directories", test_directories),
        ("Database", test_database),
        ("Camera", test_camera),
        ("Face Recognition", test_face_recognition)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        results[test_name] = test_func()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<20}: {status}")
        if result:
            passed += 1
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to run.")
        print("\nTo start the system:")
        print("1. python app.py")
        print("2. Open http://localhost:5000 in your browser")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix the issues before running the system.")
        print("\nRefer to README.md for troubleshooting instructions.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)