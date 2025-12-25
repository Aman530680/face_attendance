import os

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Asha530680@',
    'database': 'face_attendance_db'
}

# Camera Configuration
CAMERA_INDEX = 1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Face Recognition Configuration
FACE_TOLERANCE = 0.6
FACE_LOCATIONS_MODEL = 'hog'

# File Paths
FACE_IMAGES_DIR = 'face_images'
STATIC_DIR = 'static'
TEMPLATES_DIR = 'templates'

# Create directories if they don't exist
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)