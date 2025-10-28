from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class DomainEvent:
    eventId: str
    eventType: str
    eventVersion: int
    occurredAt: str
    aggregateType: str
    aggregateId: str
    data: dict
    metadata: dict

def new_event(event_type: str, agg_type: str, agg_id: str, data: dict, version: int = 1, meta: dict | None = None):
    return DomainEvent(
        eventId=str(uuid.uuid4()),
        eventType=event_type,
        eventVersion=version,
        occurredAt=datetime.utcnow().isoformat() + "Z",
        aggregateType=agg_type,
        aggregateId=agg_id,
        data=data,
        metadata=data or {}
    ).__dict__

def anomaly_detected(zona:str, score: float):
    return new_event("AnomalyDetected", "Zone",f"zone:{zona}", {"zona": zona, "score":score})

def anomaly_resolved(zona: str):
    return new_event("AnomalyResolved","Zone", f"zone:{zona}",{"zona": zona})

def alert_created(alert_id: str, zona: str, severity:str):
    return new_event("AlertCreated","Alert", alert_id,{"zona": zona, "severity": severity})

def alert_closed(alert_id: str, zona: str):
    return new_event("AlertClosed","Alert",alert_id,{"zona": zona})