from domain.events import anomaly_detected
from shared.kafka_utils import publish

def emit_anomalies(pdf):
    # Regla simple: densidad_media > 70 → AnomalyDetected
    for _, r in pdf.iterrows():
        if float(r.get("densidad_media", 0)) > 70:
            evt = anomaly_detected(zona=r["zona"], score=float(r["densidad_media"]))
            publish("traffic.anomalies.v1", evt, key=r["zona"])
