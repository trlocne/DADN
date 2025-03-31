from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import os
from datetime import datetime
import shutil
import time
from imutils import paths
import face_recognition
import pickle
import cv2
import numpy as np
import threading
import concurrent.futures
import paho.mqtt.client as mqtt
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


# Adafruit IO Configuration
ADAFRUIT_USERNAME = "vmquan1401"
ADAFRUIT_ACCESS_TOKEN = os.getenv("ADA_FRUIT_IO_KEY")
AIO_FEED = f"{ADAFRUIT_USERNAME}/feeds/BBC_DETECT"
BROKER = "io.adafruit.com"
PORT = 1883

# MQTT Setup
client = mqtt.Client()
client.username_pw_set(ADAFRUIT_USERNAME, ADAFRUIT_ACCESS_TOKEN)
client.connect(BROKER, PORT, 60)
client.loop_start()

def send_status_to_adafruit(status):
    client.publish(AIO_FEED, status)
    print(f"[INFO] Sent status to Adafruit: {status}")


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

unique_img = 0
known_face_encodings = []
known_face_names = []


def load_model():
    global known_face_encodings, known_face_names
    print("[INFO] Loading encodings...")
    try: 
        with open("encodings.pickle", "rb") as f:
            data = pickle.loads(f.read())
        known_face_encodings = np.array(data["encodings"])
        known_face_names = data["names"]
    except FileNotFoundError:
        print("[ERROR] encodings.pickle file not found.")
        known_face_encodings, known_face_names = [], []
    
load_model()

def create_folder(name):
    dataset_folder = "dataset"
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)
    
    person_folder = os.path.join(dataset_folder, name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    return person_folder

@app.get("/")
async def root():
    return {"message": "Welcome to the project"}

@app.get("/users")
async def get_users():
    users = os.listdir("dataset")
    return users

@app.post("/upload-faces/")
async def upload_faces(
    name: str,
    files: List[UploadFile] = File(..., max_length=5)
):
    global unique_img
    if len(files) != 5:
        raise HTTPException(status_code=400, detail="Exactly 5 images are required")
    
    folder = create_folder(name)
    saved_files = []
    
    try:
        for file in files:
            if not file.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not an image")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}_{file.filename.split('.')[0]}_{unique_img}.jpg"
            unique_img = unique_img + 1
            filepath = os.path.join(folder, filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_files.append(filepath)
            
        return {
            "message": f"Successfully saved 5 images for {name}",
            "saved_files": saved_files
        }
    except Exception as e:
        for saved_file in saved_files:
            if os.path.exists(saved_file):
                os.remove(saved_file)
        raise HTTPException(status_code=500, detail=str(e))

def create_folder(name):
    dataset_folder = "dataset"
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)
    
    person_folder = os.path.join(dataset_folder, name)
    if not os.path.exists(person_folder):
        os.makedirs(person_folder)
    return person_folder

def capture_photos(name: str):
    global unique_img
    folder = create_folder(name)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

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
            filepath = os.path.join(folder, filename)
            cv2.imwrite(filepath, frame)
            print(f"Photo {photo_count} saved: {filepath}")
        
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"Photo capture completed. {photo_count} photos saved for {name}.")

@app.get("/capture-photos/{name}")
async def capture(name: str):
    try:
        capture_photos(name)
        return {"message": f"Photo capture completed. Photos saved for {name}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def train_face_detect():
    print("[INFO] start processing faces...")
    imagePaths = list(paths.list_images("dataset"))
    knownEncodings = []
    knownNames = []

    for (i, imagePath) in enumerate(imagePaths):
        print(f"[INFO] processing image {i + 1}/{len(imagePaths)}")
        name = imagePath.split(os.path.sep)[-2]

        # Đọc ảnh bằng OpenCV thay vì face_recognition.load_image_file
        image = cv2.imread(imagePath)

        # Kiểm tra nếu ảnh không đọc được
        if image is None:
            print(f"[ERROR] Could not read image: {imagePath}")
            continue

        try:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            rgb = rgb.astype(np.uint8)

            if rgb.dtype != "uint8":
                print(f"[WARNING] Ảnh {imagePath} không phải uint8. Đang chuyển đổi...")
                rgb = rgb.astype(np.uint8)

            boxes = face_recognition.face_locations(rgb, model="hog")

            if len(boxes) == 0:
                print("[WARNING] Không tìm thấy khuôn mặt nào trong ảnh!")
            else:
                print(f"[INFO] Số khuôn mặt tìm thấy: {len(boxes)}")

            encodings = face_recognition.face_encodings(rgb, boxes)

        except Exception as e:
            print(f"[ERROR] Failed to encode image: {imagePath} - {str(e)}")
            continue

        for encoding in encodings:
            knownEncodings.append(encoding)
            knownNames.append(name)

    if not knownEncodings:
        print("[WARNING] No faces were encoded. Check your input images.")
        return

    print("[INFO] serializing encodings...")
    data = {"encodings": knownEncodings, "names": knownNames}
    with open("encodings.pickle", "wb") as f:
        f.write(pickle.dumps(data))

    print("[INFO] Training complete. Encodings saved to 'encodings.pickle'")

@app.get("/train_model/face_detect")
async def train_model_face():
    try:
        train_face_detect()
        load_model()
        return {"message": "Training model is completed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def face_detect_process():
    cv_scaler = 2
    face_results = []
    frame_count = 0
    start_time = time.time()
    fps = 0
    lock = threading.Lock()
    count = 0
    detection_complete = False
    detection_sent = False 

    frame_skip = 2
    frame_counter = 0

    nameDetect = "Unknown"

    def process_frame(frame):
        global known_face_encodings, known_face_names
        nonlocal cv_scaler, face_results, lock, count, detection_complete, detection_sent, nameDetect

        resized_frame = cv2.resize(frame, (0, 0), fx=(1/cv_scaler), fy=(1/cv_scaler))
        rgb_resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_resized_frame, model="hog")  # Dùng "cnn" nếu có GPU
        face_encodings = face_recognition.face_encodings(rgb_resized_frame, face_locations)

        detections = []
        for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
            name = "Unknown"
            confidence = 0.0
            matches = face_recognition.compare_faces(known_face_encodings, encoding)
            face_distances = face_recognition.face_distance(known_face_encodings, encoding)

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    confidence = 1 - face_distances[best_match_index]

                if confidence > 0.5 and name != "Unknown" and not detection_sent:
                    if name != nameDetect:
                        nameDetect = name
                        count = 0
                    count += 1
                    if count >= 7:
                        detection_sent = True
                        send_status_to_adafruit(name)
                        time.sleep(1)
                        send_status_to_adafruit("Unknown")
                        detection_complete = True
                        return

            detections.append((left * cv_scaler, top * cv_scaler, right * cv_scaler, bottom * cv_scaler, name, confidence))

        with lock:
            face_results[:] = detections

    def draw_results(frame):
        nonlocal lock, face_results
        with lock:
            for left, top, right, bottom, name, confidence in face_results:
                left, top, right, bottom = map(int, [left, top, right, bottom])
                cv2.rectangle(frame, (left, top), (right, bottom), (244, 42, 3), 2)
                text = f"{name} ({confidence:.2f})"
                cv2.putText(frame, text, (left + 6, top - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return frame

    def calculate_fps():
        nonlocal frame_count, start_time, fps
        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time > 1:
            fps = frame_count / elapsed_time
            frame_count = 0
            start_time = time.time()
        return fps

    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    video_capture.set(cv2.CAP_PROP_FPS, 30)

    for _ in range(5):
        ret, _ = video_capture.read()
        if not ret:
            print("Error: Camera failed to start.")
            return {"message": "Camera failed to start"}

    process_this_frame = True
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    while not detection_complete:
        ret, frame = video_capture.read()
        if not ret:
            break

        if frame_counter % frame_skip == 0:  # Chỉ xử lý mỗi 2 frame để tăng tốc
            executor.submit(process_frame, frame.copy())

        frame_counter += 1
        display_frame = draw_results(frame)
        current_fps = calculate_fps()
        cv2.putText(display_frame, f"FPS: {current_fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('Video', display_frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    executor.shutdown()
    return {"message": nameDetect} if detection_complete else {"message": "Unknown"}

@app.get("/face_detect")
async def face_detect():
    return face_detect_process()

@app.delete("/delete/{name}")
async def delete_user(name: str):
    try:
        folder = os.path.join("dataset", name)
        if not os.path.exists(folder):
            raise HTTPException(status_code=404, detail="User not found")
            
        shutil.rmtree(folder)
        print(f"[INFO] Deleted user {name}. Retraining model...")
        
        remaining_users = os.listdir("dataset")
        if remaining_users:
            train_model_face()
            return load_model()
        else:
            if os.path.exists("encodings.pickle"):
                os.remove("encodings.pickle")
            return {"message": "Last user deleted, encodings file removed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)