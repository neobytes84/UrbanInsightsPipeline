from pymongo import MongoClient, ASCENDING
import os

URI = os.getenv("MONGO_URI","mongodb://localhost:27017")
DB  = os.getenv("MONGO_DB","urban_insights")

client = MongoClient(URI)
db = client[DB]

print("→ Asegurando índices…")

# metrics: upsert idempotente por ventana
db["metrics"].create_index([("zona", ASCENDING), ("win_start", ASCENDING), ("win_end", ASCENDING)], unique=True)

# alerts_state: estado por alerta
db["alerts_state"].create_index([("alertId", ASCENDING)], unique=True)

# events_raw (si usas Event Store)
db["events_raw"].create_index([("eventId", ASCENDING)], unique=True)

print("✅ Índices OK")
