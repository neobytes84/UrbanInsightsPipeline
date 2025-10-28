import os
from shared.kafka_utils import publish
from shared.mongo_utils import get_coll
from domain.events import alert_created, alert_closed

alerts = get_coll(coll="alerts_state")

def on_anomaly_detected(evt: dict):
    zona = evt["data"]["zona"]
    score = float(evt["data"]["score"])
    severity = "HIGH" if score > 80 else ("MEDIUM" if score > 65 else "LOW")
    alert_id = f"alert:{zona}"

    # idempotencia: si ya está OPEN/ACK, no dupliques
    found = alerts.find_one({"alertId": alert_id, "status": {"$in": ["OPEN","ACK"]}})
    if found:
        return
    alerts.update_one({"alertId": alert_id}, {"$set": {"alertId": alert_id, "zona": zona, "status": "OPEN"}}, upsert=True)
    publish("alerts.domain.v1", alert_created(alert_id, zona, severity), key=alert_id)

def on_anomaly_resolved(evt: dict):
    zona = evt["data"]["zona"]
    alert_id = f"alert:{zona}"
    found = alerts.find_one({"alertId": alert_id, "status": "OPEN"})
    if not found:
        return
    alerts.update_one({"alertId": alert_id}, {"$set": {"status": "CLOSED"}})
    publish("alerts.domain.v1", alert_closed(alert_id, zona), key=alert_id)
