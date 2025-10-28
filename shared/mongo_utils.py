import os
from pymongo import MongoClient, ASCENDING

def get_coll(db="urban_insights", coll="metrics"):
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    client = MongoClient(uri)
    return client[db][coll]

def ensure_indexes():
    m = get_coll(coll="metrics")
    m.create_index([("zona", ASCENDING), ("win_start", ASCENDING), ("win_end", ASCENDING)], unique=True)
    
    # event_raw: eventId
    e = get_coll(coll="event_raw")
    e.create_index([("eventId", ASCENDING)], unique=True)
    
    # alert_state: alertId
    a = get_coll(coll="alert_state")
    a.create_index([("alertId", ASCENDING)], unique=True)