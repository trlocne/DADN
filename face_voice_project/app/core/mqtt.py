from typing import Dict, List, Callable
import paho.mqtt.client as mqtt
from .config import settings

class MQTTObserver:
    def update(self, topic: str, message: str) -> None:
        pass

class MQTTService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.client = mqtt.Client()
        self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_ACCESS_TOKEN)
        self.observers: Dict[str, List[MQTTObserver]] = {}
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        self.connect()

    def connect(self):
        try:
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"[ERROR] Failed to connect to MQTT broker: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        print(f"[INFO] Connected to MQTT broker with result code {rc}")
        for topic in self.observers.keys():
            client.subscribe(topic)

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        message = msg.payload.decode()
        if topic in self.observers:
            for observer in self.observers[topic]:
                observer.update(topic, message)

    def attach(self, topic: str, observer: MQTTObserver):
        if topic not in self.observers:
            self.observers[topic] = []
            self.client.subscribe(topic)
        self.observers[topic].append(observer)

    def detach(self, topic: str, observer: MQTTObserver):
        if topic in self.observers:
            self.observers[topic].remove(observer)
            if not self.observers[topic]:
                del self.observers[topic]
                self.client.unsubscribe(topic)

    def publish(self, topic: str, message: str):
        self.client.publish(topic, message)
        print(f"[INFO] Published to {topic}: {message}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()