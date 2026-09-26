#!/usr/bin/env bash
set -euo pipefail

RESTORE_FILE="${1:-backup.sql}"

if [ ! -f "${RESTORE_FILE}" ]; then
    echo "[FAIL] Restore file '${RESTORE_FILE}' does not exist."
    exit 1
fi

echo "Restoring database from '${RESTORE_FILE}'..."

# Restore SQL dump into the postgres container
cat "${RESTORE_FILE}" | docker exec -i postgres psql -U barq_app -d barq_tasks > /dev/null

echo "[PASS] Database successfully restored from ${RESTORE_FILE}"
exit 0
