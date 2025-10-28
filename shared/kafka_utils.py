import json, os
from kafka import KafkaProducer

_producer = None

def _get_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=os.environ.get('KAFKA_BROKERS', 'localhost:9092'),
            acks='all', linger_ms=50, retries=3,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v:str(v).encode('utf-8'),
        )
        return _producer

def send_message(topic, message, key=None):
    producer = _get_producer()
    producer.send(topic, key=key, value=message)
    producer.flush()

def publish(topic:str, event: dict, key: str= ""):
    _get_producer().send(topic, value=event, key=(key or event.get("aggregateId", "")))