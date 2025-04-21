import asyncio
from app.utils.recognition_utils import VoiceRecognitionUtils
from app.core.mqtt import MQTTService
from app.core.config import settings

listening_task = None
listening_active = False

voice_recognition = VoiceRecognitionUtils()
mqtt_service = MQTTService()

async def listen_loop():
    global listening_active
    voice_recognition.adjust_for_noise()
    
    while listening_active:
        text = voice_recognition.listen_and_recognize()
        if text:
            print(f"[INFO] Recognized: {text}")
            command = voice_recognition.parse_voice_command(text)

            if command:
                action, target = command

                if action in ["on", "off"]:
                    if target == "fan":
                        mqtt_service.publish(settings.AIO_FEED_FAN, "1" if action == "on" else "0")
                    elif target == "light":
                        mqtt_service.publish(settings.AIO_FEED_LED, "1" if action == "on" else "0")

                elif action == "set_speed" and isinstance(target, int):
                    mqtt_service.publish(settings.AIO_FEED_CONTROL, str(target))
                    print(f"[INFO] Fan speed set to {target}")

        await asyncio.sleep(0.5)

def start_listening():
    global listening_task, listening_active
    if not listening_active:
        listening_active = True
        listening_task = asyncio.create_task(listen_loop())

def stop_listening():
    global listening_task, listening_active
    listening_active = False
    if listening_task and not listening_task.done():
        listening_task.cancel()
        print("[INFO] Listening stopped.")
