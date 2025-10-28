import os, json
from kafka import KafkaConsumer
from shared.mongo_utils import get_coll, ensure_indexes

def run():
    ensure_indexes()
    coll = get_coll(coll="events_raw")
    cons = KafkaConsumer(
        os.getenv("RAW_TOPIC","traffic.raw.v1"),
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS","localhost:9092"),
        group_id="raw-store",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        enable_auto_commit=True,
    )
    for msg in cons:
        evt = msg.value
        # idempotencia por eventId
        coll.update_one({"eventId": evt["eventId"]}, {"$setOnInsert": evt}, upsert=True)

if __name__ == "__main__":
    run()
