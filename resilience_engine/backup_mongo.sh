#!/usr/bin/env bash
set -e
TS=$(date +%Y%m%d_%H%M%S)
mkdir -p backups
docker exec -i $(docker ps -q -f name=mongo) mongodump --archive > backups/mongo_$TS.archive
echo "✅ Backup en backups/mongo_$TS.archive"
# restore: docker exec -i <mongo_id> mongorestore --archive < backups/mongo_x.archive
