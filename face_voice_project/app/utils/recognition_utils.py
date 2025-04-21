import face_recognition
import numpy as np
import speech_recognition as sr
from typing import List, Tuple, Optional
import re

class FaceRecognitionUtils:
    @staticmethod
    def detect_faces(rgb_frame: np.ndarray, model: str = "hog") -> List[Tuple[int, int, int, int]]:
        """Detect faces in an RGB frame and return their locations."""
        return face_recognition.face_locations(rgb_frame, model=model)
    
    @staticmethod
    def encode_faces(rgb_frame: np.ndarray, face_locations: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """Generate face encodings for detected faces."""
        return face_recognition.face_encodings(rgb_frame, face_locations)
    
    @staticmethod
    def compare_faces(known_encodings: List[np.ndarray], 
                     face_encoding: np.ndarray, 
                     tolerance: float = 0.6) -> Tuple[List[bool], List[float]]:
        """Compare a face encoding against a list of known encodings."""
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance)
        distances = face_recognition.face_distance(known_encodings, face_encoding)
        return matches, distances

class VoiceRecognitionUtils:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(device_index=0)
    
    def adjust_for_noise(self, duration: float = 1.0):
        """Adjust recognizer for ambient noise."""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)
    
    def listen_and_recognize(self, language: str = "vi-VN") -> Optional[str]:
        """Listen for speech and convert to text."""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source)
                return self.recognizer.recognize_google(audio, language=language).lower()
        except sr.UnknownValueError:
            print("Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            return None

    def parse_voice_command(self, text: str) -> Optional[Tuple[str, str]]:
        """Parse voice command text into command and value."""
        if not text:
            return None

        text = text.lower()

        match = re.search(r"tốc độ quạt\s*(\D*)\s*(\d+)", text)
        if match and match.group(2):
            speed = int(match.group(2))
            print(speed)
            if 0 < speed < 100:
                return "set_speed", speed

        if "bật quạt" in text:
            return "on", "fan"
        elif "tắt quạt" in text:
            return "off", "fan"
        elif "bật đèn" in text:
            return "on", "light"
        elif "tắt đèn" in text:
            return "off", "light"

        return None