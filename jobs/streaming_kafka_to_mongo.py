# jobs/streaming_kafka_to_mongo.py
# PySpark Structured Streaming: lee JSON desde Kafka, calcula métricas por ventana,
# guarda en MongoDB y emite eventos de anomalía a Kafka (traffic.anomalies.v1)

import os
import json
from datetime import datetime
from pyspark.sql import SparkSession, functions as F, types as T
from pymongo import MongoClient
from kafka import KafkaProducer

# --- Config ---
# Carga de variables desde backend.settings si existe; si no, usa defaults (.env opcional)
CFG = {
    "KAFKA_BOOTSTRAP_SERVERS": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
    "KAFKA_TOPIC": os.getenv("KAFKA_TOPIC", "traffic_stream"),  # topic de entrada
    "ANOMALIES_TOPIC": os.getenv("ANOMALIES_TOPIC", "traffic.anomalies.v1"),  # topic de salida
    "MONGO_URI": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
    "MONGO_DB": os.getenv("MONGO_DB", "urban_insights"),
    "MONGO_COLLECTION": os.getenv("MONGO_COLLECTION", "metrics"),
    "CHECKPOINT_DIR": os.getenv("CHECKPOINT_DIR", "./chk/traffic"),
}

# Garantiza carpeta de checkpoint
os.makedirs(CFG["CHECKPOINT_DIR"], exist_ok=True)

# --- Spark session ---

spark = (
    SparkSession.builder
    .appName("UrbanInsightsStreaming")
    .master("local[*]")
    # 👇 Añade el conector Spark-Kafka (versión de Spark 3.5.1 + Scala 2.12)
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1")
    .config("spark.sql.shuffle.partitions", "4")
    .config("spark.streaming.stopGracefullyOnShutdown", "true")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# --- Esquema del JSON de entrada ---
schema = T.StructType([
    T.StructField("ts", T.StringType(), True),        # ISO string
    T.StructField("zona", T.StringType(), True),
    T.StructField("velocidad", T.DoubleType(), True),
    T.StructField("densidad", T.DoubleType(), True),
])

# --- Fuente Kafka ---
raw = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", CFG["KAFKA_BOOTSTRAP_SERVERS"])
    .option("subscribe", CFG["KAFKA_TOPIC"])
    .option("startingOffsets", "latest")
    .load()
)

parsed = (
    raw.selectExpr("CAST(value AS STRING) AS value")
       .select(F.from_json("value", schema).alias("v"))
       .select(
            F.to_timestamp("v.ts").alias("ts"),
            F.col("v.zona").alias("zona"),
            F.col("v.velocidad").alias("velocidad"),
            F.col("v.densidad").alias("densidad"),
       )
       .filter(F.col("ts").isNotNull() & F.col("zona").isNotNull())
)

# --- Agregación por ventana (30s) con watermark (2m) ---
win = (
    parsed
    .withWatermark("ts", "2 minutes")
    .groupBy(F.window("ts", "30 seconds"), F.col("zona"))
    .agg(
        F.avg("velocidad").alias("velocidad_media"),
        F.avg("densidad").alias("densidad_media"),
    )
    .select(
        F.col("zona"),
        F.col("velocidad_media"),
        F.col("densidad_media"),
        F.col("window.start").alias("win_start"),
        F.col("window.end").alias("win_end"),
    )
)

# --- Conexiones a Mongo y Kafka (en foreachBatch se usa en el driver) ---
_mongo_client = None
def _mongo():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(CFG["MONGO_URI"])
    return _mongo_client[CFG["MONGO_DB"]][CFG["MONGO_COLLECTION"]]

_kafka_producer = None
def _producer():
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = KafkaProducer(
            bootstrap_servers=CFG["KAFKA_BOOTSTRAP_SERVERS"],
            acks="all",
            retries=3,
            linger_ms=50,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: (k or "").encode("utf-8"),
        )
    return _kafka_producer

# --- Reglas de anomalía (simple): densidad_media > 70 ---
def _emit_anomalies(pdf):
    if pdf is None or pdf.empty:
        return
    prod = _producer()
    for _, r in pdf.iterrows():
        try:
            dens = float(r.get("densidad_media", 0) or 0)
            if dens > 70:
                zona = str(r["zona"])
                evt = {
                    "eventId": f"anom-{zona}-{int(datetime.utcnow().timestamp()*1000)}",
                    "eventType": "AnomalyDetected",
                    "eventVersion": 1,
                    "occurredAt": datetime.utcnow().isoformat() + "Z",
                    "aggregateType": "Zone",
                    "aggregateId": f"zone:{zona}",
                    "data": {"zona": zona, "score": dens},
                    "metadata": {"source": "spark_rules"},
                }
                prod.send(CFG["ANOMALIES_TOPIC"], value=evt, key=zona)
        except Exception as e:
            print(f"[WARN] No se pudo evaluar/anunciar anomalía: {e}")

# --- foreachBatch: upsert en Mongo + emisión de anomalías ---
def write_to_mongo_and_emit(batch_df, epoch_id):
    try:
        pdf = batch_df.toPandas()
    except Exception as e:
        print(f"[ERROR] toPandas falló: {e}")
        return

    if pdf is None or pdf.empty:
        return

    coll = _mongo()

    # upserts por (zona, win_start, win_end)
    records = pdf.to_dict(orient="records")
    for r in records:
        key = {"zona": r["zona"], "win_start": r["win_start"], "win_end": r["win_end"]}
        coll.update_one(key, {"$set": r}, upsert=True)

    # reglas de anomalías → Kafka
    _emit_anomalies(pdf)

# --- Sink: foreachBatch ---
query = (
    win.writeStream
    .outputMode("update")  # usamos update para evitar volúmenes innecesarios
    .foreachBatch(write_to_mongo_and_emit)
    .option("checkpointLocation", CFG["CHECKPOINT_DIR"])
    .start()
)

print("✅ Streaming iniciado. Leyendo de Kafka y escribiendo en Mongo…")
query.awaitTermination()
