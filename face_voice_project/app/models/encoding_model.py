import pickle
import numpy as np
from typing import List, Dict, Any
from pathlib import Path

class EncodingModel:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.encodings: List[np.ndarray] = []
        self.names: List[str] = []
        self.load()
    
    def load(self) -> None:
        """Load face encodings from pickle file."""
        try:
            if Path(self.file_path).exists():
                with open(self.file_path, "rb") as f:
                    data = pickle.loads(f.read())
                self.encodings = np.array(data["encodings"])
                self.names = data["names"]
        except Exception as e:
            print(f"[ERROR] Failed to load encodings: {e}")
            self.encodings = []
            self.names = []
    
    def save(self) -> None:
        """Save face encodings to pickle file."""
        try:
            data = {"encodings": self.encodings, "names": self.names}
            with open(self.file_path, "wb") as f:
                f.write(pickle.dumps(data))
        except Exception as e:
            print(f"[ERROR] Failed to save encodings: {e}")
    
    def add_encoding(self, encoding: np.ndarray, name: str) -> None:
        """Add a new face encoding."""
        self.encodings.append(encoding)
        self.names.append(name)
    
    def remove_encodings_by_name(self, name: str) -> None:
        """Remove all encodings for a given name."""
        indices = [i for i, n in enumerate(self.names) if n != name]
        self.encodings = [self.encodings[i] for i in indices]
        self.names = [self.names[i] for i in indices]
    
    def clear(self) -> None:
        """Clear all encodings."""
        self.encodings = []
        self.names = []
        if Path(self.file_path).exists():
            Path(self.file_path).unlink()
    
    def get_encodings(self) -> List[np.ndarray]:
        """Get all face encodings."""
        return self.encodings
    
    def get_names(self) -> List[str]:
        """Get all names."""
        return self.names