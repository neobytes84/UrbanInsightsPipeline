# RUNBOOK — Urban Insights Pipeline (Resilience & Incidents)

## 0. Resumen del sistema
- Ingesta: Producer → Kafka (`traffic_stream`)
- Procesamiento: PySpark Structured Streaming (ventana 30s, watermark 2m)
- Persistencia de lectura: MongoDB (`urban_insights.metrics`, `alerts_state`)
- Eventos dominio (EDA): `traffic.anomalies.v1`, `alerts.domain.v1`
- Checkpointing: `./chk/traffic` (exactly-once con upsert idempotente)

## 1. Detección (qué vigilar)
- **Kafka**: `docker compose ps`, healthcheck, `consumer-groups`
- **Mongo**: `mongosh` ping, errores de escritura en logs de Spark
- **Streaming**: logs de Spark; que el microbatch siga corriendo sin retraso excesivo
- **UI**: ausencia de nuevos puntos / métricas

## 2. Contención inmediata
1) Pausar productor para drenar:
   ```bash
   curl -X POST http://localhost:8000/pause
