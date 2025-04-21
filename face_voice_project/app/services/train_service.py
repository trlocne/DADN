import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List
from imutils import paths
from ..utils.recognition_utils import FaceRecognitionUtils
from ..models.encoding_model import EncodingModel
from ..core.config import settings

class TrainService:
    def __init__(self):
        self.encoding_model = EncodingModel(settings.ENCODINGS_FILE)
    
    def train_model(self) -> bool:
        """Train face recognition model with all images in dataset."""
        print("[INFO] Starting face recognition training...")
        image_paths = list(paths.list_images(settings.DATASET_PATH))
        
        if not image_paths:
            print("[WARNING] No images found in dataset")
            return False
        
        known_encodings = []
        known_names = []
        
        for (i, image_path) in enumerate(image_paths):
            print(f"[INFO] Processing image {i + 1}/{len(image_paths)}")
            name = Path(image_path).parent.name
            
            try:
                # Load and convert image
                image = cv2.imread(str(image_path))
                if image is None:
                    print(f"[ERROR] Could not read image: {image_path}")
                    continue
                
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Detect faces and generate encodings
                face_locations = FaceRecognitionUtils.detect_faces(
                    rgb_image,
                    model=settings.FACE_DETECTION_MODEL
                )
                
                if not face_locations:
                    print(f"[WARNING] No faces found in {image_path}")
                    continue
                
                encodings = FaceRecognitionUtils.encode_faces(rgb_image, face_locations)
                
                # Add encodings to lists
                for encoding in encodings:
                    known_encodings.append(encoding)
                    known_names.append(name)
                    
            except Exception as e:
                print(f"[ERROR] Failed to process {image_path}: {e}")
                continue
        
        if not known_encodings:
            print("[ERROR] No faces were encoded")
            return False
        
        # Save encodings
        self.encoding_model.encodings = known_encodings
        self.encoding_model.names = known_names
        self.encoding_model.save()
        
        print(f"[INFO] Training complete. Encoded {len(known_encodings)} faces")
        return True
    
    def get_training_stats(self) -> Dict[str, int]:
        """Get statistics about trained model."""
        stats = {}
        for name in self.encoding_model.get_names():
            if name in stats:
                stats[name] += 1
            else:
                stats[name] = 1
        return stats