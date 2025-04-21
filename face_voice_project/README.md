# Face and Voice Control System

A sophisticated system that combines face recognition and voice control capabilities for smart home automation. This project utilizes advanced computer vision and speech recognition technologies to provide a seamless and secure way to control your smart home devices.

## Features

- **Face Recognition**
  - Real-time face detection and recognition
  - High accuracy with confidence threshold
  - Support for multiple user profiles
  - Automatic device control based on face recognition

- **Voice Control**
  - Vietnamese language support
  - Natural language processing for command interpretation
  - Voice-activated device control
  - Support for multiple command types (on/off, device selection)

## System Architecture

The system is built using a modular architecture with the following key components:

### Core Components

1. **Face Recognition Module**
   - Uses face_recognition library for detection and encoding
   - Implements Factory pattern for service creation
   - Utilizes Observer pattern for MQTT communication
   - Real-time processing with multi-threading support

2. **Voice Recognition Module**
   - Integrates with Google Speech Recognition API
   - Command parsing and interpretation system
   - Noise adjustment capabilities

3. **MQTT Communication**
   - Real-time device state updates
   - Secure communication protocol
   - Integration with Adafruit IO

## Installation

### Prerequisites

- Python 3.7 or higher
- OpenCV compatible camera
- Microphone for voice input
- MQTT broker access (Adafruit IO account)

### Dependencies

Install the required packages using pip:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- fastapi==0.68.1
- uvicorn==0.15.0
- python-multipart==0.0.5
- paho-mqtt==1.6.1
- opencv-python==4.5.3.56
- face-recognition==1.3.0
- imutils==0.5.4
- numpy==1.21.2
- python-dotenv==0.19.0
- SpeechRecognition==3.8.1
- pyaudio==0.2.11

## Configuration

1. Create a `.env` file in the project root with your MQTT credentials:

```env
AIO_USERNAME=your_username
AIO_KEY=your_key
AIO_FEED_DETECT=your_feed_id
```

2. Configure face recognition settings in `core/config.py`:
- Adjust confidence threshold
- Set frame processing parameters
- Configure camera settings

## Usage

### Starting the System

1. Start the face recognition service:
```bash
python main.py
```

2. The system will:
- Initialize camera
- Connect to MQTT broker
- Begin face detection and recognition
- Listen for voice commands

### Voice Commands

Supported Vietnamese commands:
- "Bật đèn" - Turn on light
- "Tắt đèn" - Turn off light
- "Bật quạt" - Turn on fan
- "Tắt quạt" - Turn off fan

## API Endpoints

The system exposes FastAPI endpoints for integration:

- `POST /api/face/recognize`: Trigger face recognition
- `POST /api/voice/command`: Process voice command

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.