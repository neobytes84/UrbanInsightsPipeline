import json, os
from kafka import KafkaConsumer, KafkaProducer

BOOT  = os.getenv("KAFKA_BOOTSTRAP_SERVERS","localhost:9092")
DLQ   = os.getenv("DLQ_TOPIC","traffic.dlq.v1")
RETRY = os.getenv("RETRY_TOPIC","traffic_stream")

cons = KafkaConsumer(DLQ, bootstrap_servers=BOOT, value_deserializer=lambda m: json.loads(m.decode()))
prod = KafkaProducer(bootstrap_servers=BOOT, value_serializer=lambda v: json.dumps(v).encode())

for msg in cons:
    evt = msg.value
    print("DLQ record:", evt)
    # TODO: sanear/validar si hace falta antes de reinyectar:
    prod.send(RETRY, evt)
