#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-backup.sql}"

echo "Starting database backup to '${BACKUP_FILE}'..."

# Dump PostgreSQL database using container credentials
docker exec postgres pg_dump -U barq_app -d barq_tasks > "${BACKUP_FILE}"

if [ -s "${BACKUP_FILE}" ]; then
    echo "[PASS] Backup successfully created at ${BACKUP_FILE}"
    exit 0
else
    echo "[FAIL] Backup file is empty or was not created."
    exit 1
fi
