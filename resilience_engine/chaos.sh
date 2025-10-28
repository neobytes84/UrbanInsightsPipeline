#!/usr/bin/env bash
set -e
echo "💥 Parando Kafka 8s…"; docker stop kafka; sleep 8; docker start kafka
echo "💥 Parando Mongo 8s…"; docker stop mongo; sleep 8; docker start mongo
echo "✅ Caos terminado. Verifica que el streaming se haya recuperado (checkpoint)."
