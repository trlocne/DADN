import requests
import json
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import Schema

USERNAME = 'vmquan1401'
AIO_KEY = os.getenv("ADA_FRUIT_IO_KEY")
BASE_URL = f'https://io.adafruit.com/api/v2/{USERNAME}/feeds'
HEADERS = {'X-AIO-Key': AIO_KEY}
SCHEMA_REGISTRY_URL = 'http://localhost:8082'
SCHEMA_PATH = "../Avro_schema/"
USER = {"username": "mark12", "password": "444444"}
FEEDS = {
    "led": ['bbc-led'],
    "fan": [['bbc-fan', 'bbc-control-fan']],
    "door": [['bbc-servo', 'bbc-password']],
    "humidity": ['bbc-humidity'],
    "temperature": ['bbc-temperature']
}

SCHEMA_TOPIC = {
    "led" : "led_schema",
    "fan" : "fan_schema",
    "door" : "door_schema",
    "humidity" : "hum_schema",
    "temperature" : "tem_schema",
}

def generate_door_data(id_door, bbc_servo, password):
    return {
        "id_door": id_door,
        "bbc_servo": bbc_servo,
        "bbc_name": USER["username"],
        "bbc_password": password,
        "timestamp": datetime.now().isoformat()
    }

def generate_fan_data(id_fan, bbc_fan, bbc_control_fan):
    return {
        "id_fan": id_fan,
        "bbc_fan": bbc_fan,
        "bbc_control_fan": bbc_control_fan,
        "bbc_name": USER["username"],
        "bbc_password": USER["password"],
        "timestamp": datetime.now().isoformat()
    }

def generate_humidity_data(id_humidity, bbc_hum):
    return {
        "id_hum": id_humidity,
        "bbc_hum": bbc_hum,
        "bbc_name": USER["username"],
        "bbc_password": USER["password"],
        "timestamp": datetime.now().isoformat()
    }

def generate_led_data(id_led, bbc_led):
    return {
        "id_led": id_led,
        "bbc_led": bbc_led,
        "bbc_name": USER["username"],
        "bbc_password": USER["password"],
        "timestamp": datetime.now().isoformat()
    }

def generate_temp_data(id_temp, bbc_temp):
    return {
        "id_temp": id_temp,
        "bbc_temp": bbc_temp,
        "bbc_name": USER["username"],
        "bbc_password": USER["password"],
        "timestamp": datetime.now().isoformat()
    }

def generate_data(schema, id_key, *values):
    return {
        id_key: values[0],
        **{f"bbc_{key}": val for key, val in zip(schema.split('_')[0:-1], values)},
        "timestamp": datetime.now().isoformat()
    }

def load_avro_schema(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.dumps(json.load(file))
    except Exception as e:
        print(f"Lỗi khi load schema {file_path}: {e}")
        exit(1)

def register_schemas(schema_registry_client):
    avro_serializers = {}
    for file in os.listdir(SCHEMA_PATH):
        if file.endswith(".avsc"):
            schema_path = os.path.join(SCHEMA_PATH, file)
            schema_str = load_avro_schema(schema_path)
            subject = file.replace(".avsc", "")
            try:
                if subject not in schema_registry_client.get_subjects():
                    schema_id = schema_registry_client.register_schema(subject, Schema(schema_str, "AVRO"))
                    print(f"Schema '{subject}' đã đăng ký với ID: {schema_id}")
                avro_serializers[subject] = AvroSerializer(schema_registry_client, schema_str)
            except Exception as e:
                print(f"Lỗi khi đăng ký schema {subject}: {e}")
    return avro_serializers

def get_feed_data(feed):
    try:
        response = requests.get(f'{BASE_URL}/{feed}', headers=HEADERS)
        return response.json().get("last_value") if response.status_code == 200 else None
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu từ {feed}: {e}")
        return None
#
# def main():
#     schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})
#     avro_serializers = register_schemas(schema_registry_client)
#     producer = SerializingProducer({
#         "bootstrap.servers": "localhost:9092",
#         "key.serializer": StringSerializer(),
#         "value.serializer": None
#     })
#
#     start_time = datetime.now()
#     while (datetime.now() - start_time).seconds < 10000:
#         for schema, feed_list in FEEDS.items():
#             for feed in feed_list:
#                 id = None;
#                 if isinstance(feed, list):
#                     values = [get_feed_data(f) for f in feed]
#                     id =  feed[0]
#                 else:
#                     values = [get_feed_data(feed)]
#                     id = feed
#
#
#                 if None not in values:
#                     if schema == "led":
#                         data = generate_led_data(id, values[0])
#                     elif schema == "fan":
#                         data = generate_fan_data(id, values[0], values[1])
#                     elif schema == "door":
#                         data = generate_door_data(id, values[0], values[1])
#                     elif schema == "humidity":
#                         data = generate_humidity_data(id, float(values[0]))
#                     elif schema == "temperature":
#                         data = generate_temp_data(id, float(values[0]))
#                     print(f"Avro value: {data}")
#                     try:
#                         avro_data = avro_serializers[SCHEMA_TOPIC[schema]](data, SerializationContext(schema, MessageField.VALUE))
#                         producer.produce(topic=SCHEMA_TOPIC[schema], value=avro_data, on_delivery=lambda err, msg: print(f"Lỗi: {err}" if err else f"Gửi thành công: {msg.topic()} [{msg.partition()}] @ {msg.offset()}"))
#                         producer.poll(0.01)
#                     except Exception as e:
#                         print(f"Lỗi khi gửi dữ liệu Kafka: {e}")
#         time.sleep(1)
#
#     producer.flush()


def fetch_and_process_feed(schema, feed_list, avro_serializers, producer):
    for feed in feed_list:
        id = None
        if isinstance(feed, list):
            values = [get_feed_data(f) for f in feed]
            id = feed[0]
        else:
            values = [get_feed_data(feed)]
            id = feed

        if None not in values:
            if schema == "led":
                data = generate_led_data(id, values[0])
            elif schema == "fan":
                data = generate_fan_data(id, values[0], values[1])
            elif schema == "door":
                data = generate_door_data(id, values[0], values[1])
            elif schema == "humidity":
                data = generate_humidity_data(id, float(values[0]))
            elif schema == "temperature":
                data = generate_temp_data(id, float(values[0]))

            print(f"Avro value: {data}")
            try:
                avro_data = avro_serializers[SCHEMA_TOPIC[schema]](
                    data, SerializationContext(schema, MessageField.VALUE)
                )
                producer.produce(
                    topic=SCHEMA_TOPIC[schema],
                    value=avro_data,
                    on_delivery=lambda err, msg: print(f"Lỗi: {err}" if err else f"Gửi thành công: {msg.topic()} [{msg.partition()}] @ {msg.offset()}")
                )
                producer.poll(0.01)
            except Exception as e:
                print(f"Lỗi khi gửi dữ liệu Kafka: {e}")

def main():
    schema_registry_client = SchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})
    avro_serializers = register_schemas(schema_registry_client)
    producer = SerializingProducer({
        "bootstrap.servers": "localhost:9092",
        "key.serializer": StringSerializer(),
        "value.serializer": None
    })

    start_time = datetime.now()
    with ThreadPoolExecutor(max_workers=5) as executor:  # 5 luồng chạy song song
        while (datetime.now() - start_time).seconds < 10000:
            futures = []
            for schema, feed_list in FEEDS.items():
                futures.append(executor.submit(fetch_and_process_feed, schema, feed_list, avro_serializers, producer))
            for future in futures:
                future.result()
            time.sleep(1)

    producer.flush()

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
