import os, json
from kafka import KafkaConsumer
from domain.policies import on_anomaly_detected, on_anomaly_resolved

consumer = KafkaConsumer(
    "traffic.anomalies.v1",
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS","localhost:9092"),
    group_id="alerts-policy",
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    enable_auto_commit=True,
)

def run():
    for msg in consumer:
        evt = msg.value
        et = evt.get("eventType")
        if et == "AnomalyDetected":
            on_anomaly_detected(evt)
        elif et == "AnomalyResolved":
            on_anomaly_resolved(evt)

if __name__ == "__main__":
    run()
