import json, random, threading, time
from datetime import datetime, timezone
from kafka import KafkaProducer
from backend.settings import get_settings

class TrafficProducer:
    def __init__(self):
        self.cfg = get_settings()
        self._running = False
        self._lock = threading.Lock()
        self._thread = None
        self.producer = KafkaProducer(
            bootstrap_servers=self.cfg.KAFKA_BOOTSTRAP_SERVERS,
            acks="all",
            retries=3,
            linger_ms=50,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: (k or "").encode("utf-8"),
        )

    def _event(self):
        return {
            "ts": datetime.now(timezone.utc).isoformat(),
            "zona": random.choice(["Norte","Sur","Este","Oeste","Centro"]),
            "velocidad": max(0.0, random.gauss(35, 9)),
            "densidad": max(0.0, random.gauss(55, 15)),
        }

    def _run(self):
        interval = get_settings().EVENT_INTERVAL_MS / 1000.0
        while self.is_running():
            evt = self._event()
            key = evt["zona"]
            self.producer.send(self.cfg.KAFKA_TOPIC, value=evt, key=key)
            time.sleep(interval)

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def start(self):
        with self._lock:
            if self._running: return
            self._running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False

producer_singleton = TrafficProducer()
