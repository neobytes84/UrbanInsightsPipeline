
## 2) resilience_engine/watchdog.py

import os, time, socket, requests
from pymongo import MongoClient

KAFKA = os.getenv("KAFKA_BROKER", "kafka:9092")
MONGO = os.getenv("MONGO_URI", "mongodb://mongo:27017")
API   = os.getenv("CONTROL_API", "http://host.docker.internal:8000")

def tcp_check(host, port, timeout=2):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.close(); return True
    except Exception:
        return False

def check_kafka():
    host, port = KAFKA.split(":")
    return tcp_check(host, int(port))

def check_mongo():
    try:
        MongoClient(MONGO, serverSelectionTimeoutMS=2000).admin.command("ping")
        return True
    except Exception:
        return False

def try_recover():
    # Reintenta levantar productor si está parado
    try:
        st = requests.get(f"{API}/status", timeout=2).json()
        if not st.get("running"):
            requests.post(f"{API}/play", timeout=2)
    except Exception:
        pass

if __name__ == "__main__":
    while True:
        ok_k = check_kafka()
        ok_m = check_mongo()
        if not ok_k or not ok_m:
            print(f"[RESILIENCE] kafka={ok_k} mongo={ok_m} → intentar recuperación…", flush=True)
            try_recover()
        time.sleep(5)
