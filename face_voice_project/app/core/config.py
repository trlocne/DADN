import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MQTT_BROKER = os.getenv("MQTT_BROKER", "io.adafruit.com")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "vmquan1401")
    MQTT_ACCESS_TOKEN = os.getenv("MQTT_ACCESS_TOKEN", "aio_PyFj66OZCXasRcVfTE3jeex9UcIj")
    
    AIO_FEED_DETECT = f"{MQTT_USERNAME}/feeds/BBC_DETECT"
    AIO_FEED_FAN = f"{MQTT_USERNAME}/feeds/BBC_FAN"
    AIO_FEED_LED = f"{MQTT_USERNAME}/feeds/BBC_LED"
    AIO_FEED_CONTROL = f"{MQTT_USERNAME}/feeds/BBC_CONTROL_FAN"
    
    FACE_DETECTION_MODEL = "hog"
    FACE_CONFIDENCE_THRESHOLD = 0.5
    FACE_DETECTION_COUNT = 7
    
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    FRAME_SKIP = 2
    
    DATASET_PATH = "dataset"
    ENCODINGS_FILE = "encodings.pickle"
    
    API_HOST = "localhost"
    API_PORT = 8000

settings = Settings()