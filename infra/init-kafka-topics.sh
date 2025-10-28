#!/usr/bin/env bash
set -e

BROKER=${1:-localhost:9092}

topics=(
  "traffic.raw.v1"
  "traffic.metrics.v1"
  "traffic.anomalies.v1"
  "alerts.domain.v1"
)

for t in "${topics[@]}"; do
  echo "Creating topic: $t"
  docker exec -it kafka kafka-topics --create \
    --if-not-exists \
    --topic "$t" \
    --bootstrap-server kafka:9092 \
    --replication-factor 1 \
    --partitions 1 || true
done

echo "Topics ensured."
