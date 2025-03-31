from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sounddevice as sd
import numpy as np
import tensorflow as tf
from SpeechModels import AttRNNSpeechModel
from pydantic import BaseModel
from typing import Dict, Optional
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
CHANNELS = 1
RATE = 16000

# Command categories
GSCmdV2Categs = {
    'unknown': 0, 'silence': 0, '_unknown_': 0, '_silence_': 0, '_background_noise_': 0,
    'yes': 2, 'no': 3, 'up': 4, 'down': 5, 'left': 6, 'right': 7, 'on': 8, 'off': 9,
    'stop': 10, 'go': 11, 'zero': 12, 'one': 13, 'two': 14, 'three': 15, 'four': 16,
    'five': 17, 'six': 18, 'seven': 19, 'eight': 20, 'nine': 1, 'backward': 21,
    'bed': 22, 'bird': 23, 'cat': 24, 'dog': 25, 'follow': 26, 'forward': 27,
    'happy': 28, 'house': 29, 'learn': 30, 'marvin': 31, 'sheila': 32, 'tree': 33,
    'visual': 34, 'wow': 35
}
command_list = {v: k for k, v in GSCmdV2Categs.items() if v != 0}

# Load model
model = AttRNNSpeechModel(36, samplingrate=RATE, inputLength=RATE)
model.load_weights('model-attRNN.h5')

# Store last 10 commands with timestamps
command_history = []

def record_audio():
    """Record audio for 1 second"""
    seconds = 1
    audio = sd.rec(int(seconds * RATE), samplerate=RATE, channels=CHANNELS, dtype=np.int16)
    sd.wait()
    return np.squeeze(audio)

def predict_audio(audio_data: np.ndarray) -> Dict[str, float]:
    """Predict command from audio data"""
    audio = audio_data / 32768  # Normalize
    sig = tf.convert_to_tensor(audio)
    sig = np.expand_dims(sig, axis=0)

    prediction = model.predict(sig, verbose=0)
    probs = tf.nn.softmax(prediction, axis=1)
    prob, index = tf.reduce_max(probs, axis=1), tf.argmax(probs, axis=1)
    
    confidence = float(prob.numpy()[0])
    command = command_list[index.numpy()[0]] if confidence > 0.07 else "unknown"
    
    return {"command": command, "confidence": confidence}

@app.get("/")
async def root():
    return {"message": "Speech Command Recognition API"}

@app.get("/status")
async def get_status():
    return {"status": "running", "model_loaded": True}

@app.get("/commands")
async def get_available_commands():
    return {"commands": list(command_list.values())}

@app.get("/listen")
async def listen_command():
    try:
        audio = record_audio()
        result = predict_audio(audio)
        
        if result["confidence"] > 0.07:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            command_entry = {
                "command": result["command"],
                "confidence": result["confidence"],
                "timestamp": timestamp
            }
            command_history.append(command_entry)
            if len(command_history) > 10:
                command_history.pop(0)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_command_history():
    return {"history": command_history}

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8001, reload=True)