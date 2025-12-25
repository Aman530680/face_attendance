import face_recognition
import cv2
import numpy as np
import pickle
import os
from config import FACE_TOLERANCE, FACE_LOCATIONS_MODEL

class FaceRecognitionEngine:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_student_ids = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load all approved student face encodings from database"""
        from db import DatabaseManager
        db = DatabaseManager()
        students = db.get_approved_students()
        
        self.known_face_encodings = []
        self.known_face_student_ids = []
        
        for student in students:
            if student['face_encoding']:
                try:
                    # Convert string back to numpy array
                    encoding = np.fromstring(student['face_encoding'], sep=',')
                    self.known_face_encodings.append(encoding)
                    self.known_face_student_ids.append(student['student_id'])
                except Exception as e:
                    print(f"Error loading encoding for student {student['student_id']}: {e}")
        
        print(f"Loaded {len(self.known_face_encodings)} face encodings")
        db.close()
    
    def encode_face_from_image(self, image_path):
        """Generate face encoding from image file"""
        try:
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            else:
                print("No face found in the image")
                return None
        except Exception as e:
            print(f"Error encoding face from image: {e}")
            return None
    
    def encode_face_from_frame(self, frame):
        """Generate face encoding from camera frame"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_frame)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            else:
                return None
        except Exception as e:
            print(f"Error encoding face from frame: {e}")
            return None
    
    def recognize_face(self, frame):
        """Recognize face in the given frame"""
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_frame, model=FACE_LOCATIONS_MODEL)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            recognized_students = []
            
            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Compare with known faces
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=FACE_TOLERANCE
                )
                
                student_id = None
                
                if True in matches:
                    # Find the best match
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        student_id = self.known_face_student_ids[best_match_index]
                
                recognized_students.append({
                    'student_id': student_id,
                    'face_location': face_location,
                    'confidence': 1 - (face_distances[best_match_index] if student_id else 1)
                })
            
            return recognized_students
            
        except Exception as e:
            print(f"Error in face recognition: {e}")
            return []
    
    def detect_faces(self, frame):
        """Detect faces in frame without recognition"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame, model=FACE_LOCATIONS_MODEL)
            return face_locations
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []
    
    def save_face_image(self, frame, student_id, face_location=None):
        """Save face image to file"""
        try:
            if face_location:
                top, right, bottom, left = face_location
                face_image = frame[top:bottom, left:right]
            else:
                face_image = frame
            
            filename = f"face_images/{student_id}.jpg"
            cv2.imwrite(filename, face_image)
            return filename
        except Exception as e:
            print(f"Error saving face image: {e}")
            return None
    
    def encoding_to_string(self, encoding):
        """Convert numpy array to string for database storage"""
        return ','.join(map(str, encoding))
    
    def add_new_face(self, student_id, face_encoding):
        """Add new face encoding to known faces"""
        self.known_face_encodings.append(face_encoding)
        self.known_face_student_ids.append(student_id)
        print(f"Added new face for student: {student_id}")
    
    def reload_faces(self):
        """Reload all face encodings from database"""
        self.load_known_faces()