import cv2
import threading
import time
from config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT

class CameraManager:
    def __init__(self):
        self.cap = None
        self.frame = None
        self.running = False
        self.thread = None
        self.lock = threading.Lock()
        
    def start(self):
        """Start camera capture"""
        try:
            self.cap = cv2.VideoCapture(CAMERA_INDEX)
            if not self.cap.isOpened():
                print("Error: Could not open camera")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.running = True
            self.thread = threading.Thread(target=self._capture_frames)
            self.thread.daemon = True
            self.thread.start()
            
            print("Camera started successfully")
            return True
            
        except Exception as e:
            print(f"Error starting camera: {e}")
            return False
    
    def _capture_frames(self):
        """Continuously capture frames from camera"""
        while self.running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.lock:
                        self.frame = frame.copy()
                else:
                    print("Failed to read frame from camera")
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error capturing frame: {e}")
                time.sleep(0.1)
    
    def get_frame(self):
        """Get current frame"""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None
    
    def stop(self):
        """Stop camera capture"""
        self.running = False
        if self.thread:
            self.thread.join()
        if self.cap:
            self.cap.release()
        print("Camera stopped")
    
    def is_running(self):
        """Check if camera is running"""
        return self.running and self.cap is not None and self.cap.isOpened()
    
    def draw_face_rectangle(self, frame, face_location, color=(0, 255, 0), thickness=2):
        """Draw rectangle around detected face"""
        top, right, bottom, left = face_location
        cv2.rectangle(frame, (left, top), (right, bottom), color, thickness)
        return frame
    
    def draw_text(self, frame, text, position, color=(255, 255, 255), font_scale=0.7):
        """Draw text on frame"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, text, position, font, font_scale, color, 2)
        return frame