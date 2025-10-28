from shared.mongo_utils import get_coll
from shared.kafka_utils import publish
import os

def replay(limit=1000):
    src = get_coll(coll="events_raw")
    out_topic = os.getenv("REPLAY_TOPIC","traffic.raw.v1")
    for doc in src.find().sort("occurredAt", 1).limit(limit):
        publish(out_topic, doc, key=doc.get("aggregateId",""))

if __name__ == "__main__":
    replay()
