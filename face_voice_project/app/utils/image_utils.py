import cv2
import numpy as np
from typing import Tuple, List

class ImageProcessor:
    @staticmethod
    def resize_frame(frame: np.ndarray, scale: float) -> np.ndarray:
        """Resize frame by a given scale factor."""
        return cv2.resize(frame, (0, 0), fx=1/scale, fy=1/scale)

    @staticmethod
    def convert_to_rgb(frame: np.ndarray) -> np.ndarray:
        """Convert BGR frame to RGB color space."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    @staticmethod
    def draw_face_box(frame: np.ndarray, 
                      location: Tuple[int, int, int, int], 
                      name: str, 
                      confidence: float) -> np.ndarray:
        """Draw bounding box and label for detected face."""
        left, top, right, bottom = location
        cv2.rectangle(frame, (left, top), (right, bottom), (244, 42, 3), 2)
        text = f"{name} ({confidence:.2f})"
        cv2.putText(frame, text, (left + 6, top - 6), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return frame

    @staticmethod
    def draw_fps(frame: np.ndarray, fps: float) -> np.ndarray:
        """Draw FPS counter on frame."""
        cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        return frame

class CameraManager:
    def __init__(self, width: int, height: int, fps: int):
        self.cap = None
        self.width = width
        self.height = height
        self.fps = fps

    def initialize(self) -> bool:
        """Initialize camera with specified settings."""
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Warm up the camera
        for _ in range(5):
            ret, _ = self.cap.read()
            if not ret:
                return False
        return True

    def read_frame(self) -> Tuple[bool, np.ndarray]:
        """Read a frame from the camera."""
        if self.cap is None:
            return False, None
        return self.cap.read()

    def release(self):
        """Release camera resources."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            cv2.destroyAllWindows()