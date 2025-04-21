from typing import List, Tuple, Optional
import numpy as np
import cv2
from ..utils.image_utils import ImageProcessor, CameraManager
from ..utils.recognition_utils import FaceRecognitionUtils
from ..models.encoding_model import EncodingModel
from ..core.mqtt import MQTTService, MQTTObserver
from ..core.config import settings
import time
import threading
import concurrent.futures

class FaceDetectionResult:
    def __init__(self, name: str, confidence: float, location: Tuple[int, int, int, int]):
        self.name = name
        self.confidence = confidence
        self.location = location

class FaceRecognitionFactory:
    @staticmethod
    def create_face_recognition() -> 'FaceRecognitionService':
        return FaceRecognitionService()

class FaceRecognitionService(MQTTObserver):
    def __init__(self):
        self.encoding_model = EncodingModel(settings.ENCODINGS_FILE)
        self.camera = CameraManager(
            settings.CAMERA_WIDTH,
            settings.CAMERA_HEIGHT,
            settings.CAMERA_FPS
        )
        self.mqtt_service = MQTTService()
        self.detection_count = 0
        self.current_name = "Unknown"
        self.detection_complete = False
        self.lock = threading.Lock()
        self.face_results: List[FaceDetectionResult] = []
        
    def initialize(self) -> bool:
        return self.camera.initialize()
    
    def process_frame(self, frame: np.ndarray) -> List[FaceDetectionResult]:
        # Resize and convert frame
        resized_frame = ImageProcessor.resize_frame(frame, 2)
        rgb_frame = ImageProcessor.convert_to_rgb(resized_frame)
        
        # Detect and encode faces
        face_locations = FaceRecognitionUtils.detect_faces(
            rgb_frame, 
            model=settings.FACE_DETECTION_MODEL
        )
        face_encodings = FaceRecognitionUtils.encode_faces(rgb_frame, face_locations)
        
        results = []
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            confidence = 0.0
            
            if len(self.encoding_model.get_encodings()) > 0:
                matches, face_distances = FaceRecognitionUtils.compare_faces(
                    self.encoding_model.get_encodings(),
                    face_encoding,
                    settings.FACE_CONFIDENCE_THRESHOLD
                )
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = self.encoding_model.get_names()[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        
                        if confidence > settings.FACE_CONFIDENCE_THRESHOLD:
                            if name != self.current_name:
                                self.current_name = name
                                self.detection_count = 0
                            self.detection_count += 1
                            
                            if self.detection_count >= settings.FACE_DETECTION_COUNT:
                                self.mqtt_service.publish(settings.AIO_FEED_DETECT, name)
                                time.sleep(1)
                                self.mqtt_service.publish(settings.AIO_FEED_DETECT, "Unknown")
                                self.detection_complete = True
            
            # Scale back the face locations
            scaled_location = (
                left * 2, top * 2,
                right * 2, bottom * 2
            )
            results.append(FaceDetectionResult(name, confidence, scaled_location))
        
        return results
    
    def run_detection(self) -> Optional[str]:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            frame_counter = 0
            
            while not self.detection_complete:
                ret, frame = self.camera.read_frame()
                if not ret:
                    break
                
                if frame_counter % settings.FRAME_SKIP == 0:
                    future = executor.submit(self.process_frame, frame.copy())
                    self.face_results = future.result()
                
                for result in self.face_results:
                    frame = ImageProcessor.draw_face_box(
                        frame,
                        result.location,
                        result.name,
                        result.confidence
                    )
                
                cv2.imshow('Face Recognition', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                frame_counter += 1
        
        self.camera.release()
        return self.current_name if self.detection_complete else "Unknown"
    
    
    
    def update(self, topic: str, message: str) -> None:
        # Handle MQTT messages if needed
        pass