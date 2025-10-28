#  Urban Insights Pipeline

> **Demostrador Big Data Streaming** — Pipeline completo de ingesta, procesamiento y visualización de datos en tiempo real, construido con **FastAPI**, **Redpanda (Kafka API)**, **Apache Spark Structured Streaming** y **MongoDB**.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Spark](https://img.shields.io/badge/Apache_Spark-3.5-orange)
![Kafka](https://img.shields.io/badge/Redpanda-Kafka_API-red)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0-green)
![Docker](https://img.shields.io/badge/Docker-Compose-informational)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

##  Descripción general

**Urban Insights Pipeline** simula un flujo de datos IoT / Smart City donde sensores virtuales publican eventos de tráfico en tiempo real.  
Los eventos son transmitidos mediante **Kafka/Redpanda**, procesados por **Spark Structured Streaming**, y almacenados en **MongoDB** para su análisis y detección de anomalías.

Todo el sistema está completamente **contenedorizado y orquestado con Docker Compose**, y se controla mediante un **panel web** desarrollado con `FastAPI`.

---

##  Arquitectura
┌─────────────┐ ┌────────────┐ ┌──────────────┐ ┌────────────┐
│ Productor │ ---> │ Redpanda │ ---> │ Spark Job │ ---> │ MongoDB │
│ (FastAPI) │ eventos│ (Kafka) │ stream │ (Structured │ escribe│ Métricas │
│ ▶ Play/⏸️ │ │ Broker │ │ Streaming) │ │ + Alertas │
└─────────────┘ └────────────┘ └──────────────┘ └────────────┘
↑ │
│ │
┌────────────────┐ ┌──────────────┐
│ Panel FastAPI │ <─── HTTP/JSON ───> │ Streamlit UI │
│ (Control/Logs) │ │ (opcional) │
└────────────────┘ └──────────────┘

## Levantar infraestructura
docker compose -f infra/docker-compose.yml -p urban_insights up -d

## Ejecutar la API / Panel de control

python -m venv ven
ven\Scripts\activate   # (Windows)  o  source ven/bin/activate
set PYTHONPATH=.       # export PYTHONPATH=. en Linux
uvicorn backend.api:app --reload --port 8000

Abre en el navegador 👉 http://127.0.0.1:8000/

Desde ahí podrás:

▶️ Play / Pause del productor

🚀 Start (Docker) o 🛑 Stop (Docker) del job de streaming

Ver logs en tiempo real: /stream/logs?mode=docker

4️⃣ (Opcional) Interfaz de Streamlit
streamlit run app/streamlit_app.py

🌐 Casos de uso

Analítica de tráfico urbano (Smart Cities)

Procesamiento de telemetría IoT

Detección de anomalías en tiempo real

Monitorización y alertas de infraestructura

🧱 Escalabilidad y extensiones

Integración con AWS Kinesis, GCP Pub/Sub o Azure Event Hub

Almacenamiento alternativo: Delta Lake, ClickHouse, Kudu

Dashboards BI con Grafana o Superset

ML en tiempo real con Spark MLlib o MLflow




