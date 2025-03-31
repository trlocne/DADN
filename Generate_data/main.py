import requests
import json
import time
import os
import random
from datetime import datetime, timedelta
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import Schema

user = {"username": "mark12", "password": "444444"}
USERNAME = 'vmquan1401'
AIO_KEY = os.getenv("ADA_FRUIT_IO_KEY")

feeds = {
    "led" : ['bbc-led'],
    "fan" : [['bbc-fan', 'bbc-control-fan']],
    "detect": ['bbc-detect'],
    "door": [['bbc-servo', 'bbc-password']],
    "temperature": ['bbc-temperature'],
    "pir": ['bbc-pir'],
    "humidity" : ['bbc-humidity'],
}

base_url = f'https://io.adafruit.com/api/v2/{USERNAME}/feeds'
headers = {'X-AIO-Key': AIO_KEY}

def generate_door_data(id_door, bbc_servo):
    global user
    return {
        "id_door": id_door,
        "bbc_servo": bbc_servo,
        "bbc_name": user["username"],
        "bbc_password": user["password"],
        "timestamp": datetime.time().isoformat()
    }

def generate_fan_data(id_fan: str, bbc_fan, bbc_control_fan):
    global user
    return {
        "id_fan": id_fan,
        "bbc_fan": bbc_fan,
        "bbc_control_fan": bbc_control_fan,
        "bbc_name": user["username"],
        "bbc_password": user["password"],
        "timestamp": datetime.time().isoformat()
    }

def generate_humidity_data(id_humidity: str, bbc_hum):
    global user
    return {
        "id_hum": id_humidity,
        "bbc_hum": bbc_hum,
        "bbc_name": user["username"],
        "bbc_password": user["password"],
        "timestamp": datetime.time().isoformat()
    }

def generate_led_data(id_led: str, bbc_led):
    global user
    return {
        "id_led": id_led,
        "bbc_led": bbc_led,
        "bbc_name": user["username"],
        "bbc_password": user["password"],
        "timestamp": datetime.time().isoformat()
    }

def generate_temp_data(id_temp: str, bbc_temp):
    global user
    return {
        "id_temp": id_temp,
        "bbc_temp": bbc_temp,
        "bbc_name": user["username"],
        "bbc_password": user["password"],
        "timestamp": datetime.time().isoformat()
    }

def load_avro_schema(file_path):
    if not os.path.exists(file_path):
        print(f"Lỗi: Không tìm thấy file schema {file_path}")
        exit(1)

    try:
        with open(file_path, 'r') as file:
            schema = json.load(file)
            if not schema:
                raise ValueError(f"Schema file {file_path} rỗng!")
            return json.dumps(schema)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Lỗi khi load schema {file_path}: {e}")
        exit(1)

def delivery_report(err, msg):
    if err:
        print(f"Lỗi khi gửi message: {err}")
    else:
        print(f"Message gửi thành công đến {msg.topic()} [{msg.partition()}] tại offset {msg.offset()}")

def register_schema_if_needed(schema_registry_client, subject_name, schema_str):
    try:
        subjects = schema_registry_client.get_subjects()
        if subject_name in subjects:
            print(f"Schema '{subject_name}' đã tồn tại.")
            return schema_registry_client.get_latest_version(subject_name).version

        schema = Schema(schema_str, "AVRO")
        schema_id = schema_registry_client.register_schema(subject_name, schema)
        print(f"Schema '{subject_name}' đã đăng ký với ID: {schema_id}")
        return schema_id
    except Exception as e:
        print(f"Lỗi khi đăng ký schema {subject_name}: {e}")
        return None

def main():
    # topics = ['led_events', 'fan_events', 'door_events', 'humidity_events', 'temp_events']
    schema_registry_url = 'http://localhost:8082'
    avro_schemas_path = "../Avro_schema/"
    avro_serializers = {}
    schema_registry_client = SchemaRegistryClient({'url': schema_registry_url})

    for filename in os.listdir(avro_schemas_path):
        if filename.endswith(".avsc"):
            schema_path = os.path.join(avro_schemas_path, filename)
            schema_str = load_avro_schema(schema_path)

            if schema_str:
                subject_name = filename.replace(".avsc", "")
                register_schema_if_needed(schema_registry_client, subject_name, schema_str)
                avro_serializers[subject_name] = AvroSerializer(schema_registry_client, schema_str)

    print("Danh sách AvroSerializer đã đăng ký: ", avro_serializers.keys())

    topics = list(avro_serializers.keys())

    producer_config = {
        "bootstrap.servers": "localhost:9092",
        "linger.ms": 100,
        "batch.size": 16384,
        "key.serializer": StringSerializer(),
        "value.serializer": None
    }

    generate_data = {
        "led_schema": generate_led_data,
        "fan_schema": generate_fan_data,
        "door_schema": generate_door_data,
        "hum_schema": generate_humidity_data,
        "tem_schema": generate_temp_data
    }



    producer = SerializingProducer(producer_config)
    cur_time = datetime.now()

    while (datetime.now() - cur_time).seconds < 10000:

        if len(feeds["led"]) != 0:
            for item in feeds["led"]:
                url = f'{base_url}/{item}'
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    feed_json = response.json()
                    data = generate_led_data(item, feed_json.get("last_value"))
                    topic = "led_schema"
                    avro_data = avro_serializers[topic](data, SerializationContext(topic, MessageField.VALUE))
                    print(f"Producing Avro: {data}")
                    producer.produce(topic=topic, value=avro_data, on_delivery=delivery_report)
                    producer.poll(0.1)
                else:
                    print(f"Error {response.status_code}")

        if len(feeds["fan"]) != 0:
            for item in feeds["fan"]:
                url1 = f'{base_url}/{item[0]}'
                url2 = f'{base_url}/{item[1]}'
                response1 = requests.get(url1, headers=headers)
                response2 = requests.get(url2, headers=headers)
                if response1.status_code == 200 and response2.status_code == 200:
                    feed0_json = response1.json()
                    feed1_json = response2.json()

                    data = generate_fan_data(item[0],feed0_json.get("last_value"), feed1_json.get("last_value"))
                    topic = "fan_schema"
                    avro_data = avro_serializers[topic](data, SerializationContext(topic, MessageField.VALUE))
                    print(f"Producing Avro: {data}")
                    producer.produce(topic=topic, value=avro_data, on_delivery=delivery_report)
                    producer.poll(0.1)
                else:
                    print(f"Error {response.status_code}")

        if len(feeds["door"]) != 0:
            for item in feeds["door"]:
                url1 = f'{base_url}/{item[0]}'
                url2 = f'{base_url}/{item[1]}'
                response1 = requests.get(url1, headers=headers)
                response2 = requests.get(url2, headers=headers)
                if response1.status_code == 200 and response2.status_code == 200:
                    feed0_json = response1.json()
                    feed1_json = response2.json()

                    data = generate_fan_data(item[0],feed0_json.get("last_value"), feed1_json.get("last_value"))

                    topic = "door_schema"
                    avro_data = avro_serializers[topic](data, SerializationContext(topic, MessageField.VALUE))
                    print(f"Producing Avro: {data}")
                    producer.produce(topic=topic, value=avro_data, on_delivery=delivery_report)
                    producer.poll(0.1)
                else:
                    print(f"Error {response.status_code}")

        if len(feeds["humidity"]) != 0:
            for item in feeds["humidity"]:
                url = f'{base_url}/{item[0]}'
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    feed_json = response.json()
                    data = generate_humidity_data(item[0],feed_json.get("last_value"))
                    topic = "hum_schema"

                    avro_data = avro_serializers[topic](data, SerializationContext(topic, MessageField.VALUE))
                    print(f"Producing Avro: {data}")
                    producer.produce(topic=topic, value=avro_data, on_dedelivery=delivery_report)
                    producer.poll(0.1)
                else:
                    print(f"Error {response.status_code}")

        if len(feeds["temp"]) != 0:
            for item in feeds["temp"]:
                url = f'{base_url}/{item[0]}'
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    feed_json = response.json()
                    data = generate_temp_data(item[0],feed_json.get("last_value"))
                    topic = "temp_schema"

                    avro_data = avro_serializers[topic](data, SerializationContext(topic, MessageField.VALUE))
                    print(f"Producing Avro: {data}")
                    producer.produce(topic=topic, value=avro_data, on_dedelivery=delivery_report)
                    producer.poll(0.1)

                else:
                    print(f"Error {response.status_code}")
        time.sleep(2)
        try:
            avro_data = avro_serializers[topic](data, SerializationContext(topic, MessageField.VALUE))
            print(f"Producing Avro: {data}")
            producer.produce(topic=topic, value=avro_data, on_delivery=delivery_report)
            producer.poll(0.1)
            time.sleep(1)
        except BufferError:
            print(f"Hàng đợi Producer đầy ({len(producer)} messages): Đang thử lại...")
            time.sleep(1)
        except Exception as e:
            print(f"Lỗi: {e}")
            time.sleep(10)

    producer.flush()

if __name__ == "__main__":
    main()
