import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from ..models.encoding_model import EncodingModel
from ..core.config import settings
import cv2
import time
from datetime import datetime

class UserService:
    def __init__(self):
        self.dataset_path = Path(settings.DATASET_PATH)
        self.encoding_model = EncodingModel(settings.ENCODINGS_FILE)
        
        if not self.dataset_path.exists():
            self.dataset_path.mkdir(parents=True)
    
    def get_users(self) -> List[str]:
        """Get list of all users."""
        if not self.dataset_path.exists():
            return []
        return [d.name for d in self.dataset_path.iterdir() if d.is_dir()]
    
    def create_user_folder(self, name: str) -> Path:
        """Create a new user folder."""
        user_folder = self.dataset_path / name
        if not user_folder.exists():
            user_folder.mkdir(parents=True)
        return user_folder
    
    def save_user_image(self, name: str, image_data: bytes, original_filename: str) -> str:
        """Save a user image to their folder."""
        user_folder = self.create_user_folder(name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}_{original_filename}"
        filepath = user_folder / filename
        
        with open(filepath, "wb") as f:
            f.write(image_data)
        return str(filepath)
    
    def delete_user(self, name: str) -> bool:
        """Delete a user and their data."""
        user_folder = self.dataset_path / name
        if not user_folder.exists():
            return False
        
        try:
            shutil.rmtree(user_folder)
            
            self.encoding_model.remove_encodings_by_name(name)
            self.encoding_model.save()
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to delete user {name}: {e}")
            return False
    
    def clear_all_users(self) -> bool:
        """Clear all user data."""
        try:
            if self.dataset_path.exists():
                shutil.rmtree(self.dataset_path)
                self.dataset_path.mkdir()
            
            # Clear encodings
            self.encoding_model.clear()
            return True
        except Exception as e:
            print(f"[ERROR] Failed to clear all users: {e}")
            return False

    def capture_photos(self, name: str) -> int:
        """
        Capture photos for a user using webcam.
        Returns number of photos captured.
        """
        
        user_folder = self.create_user_folder(name)
        unique_img = 0
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return 0

        time.sleep(2)
        
        photo_count = 0
        print(f"Taking photos for {name}. Press SPACE to capture, 'q' to quit.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
            
            cv2.imshow('Capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):
                photo_count += 1
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{name}_{timestamp}_{unique_img}.jpg"
                unique_img += 1
                filepath = user_folder / filename
                cv2.imwrite(str(filepath), frame)
                print(f"Photo {photo_count} saved: {filepath}")
            
            elif key == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print(f"Photo capture completed. {photo_count} photos saved for {name}.")
        
        return photo_count
