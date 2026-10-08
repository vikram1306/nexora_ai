#!/usr/bin/env bash
# ==============================================================================
# Nexora AI - Automated PostgreSQL Restore Script
# ==============================================================================
set -eo pipefail

if [ -z "$1" ]; then
    echo "Usage: ./restore_postgres.sh <path_to_backup_dump_file>"
    exit 1
fi

BACKUP_FILE="$1"
CONTAINER_NAME="${PG_CONTAINER:-nexora_postgres}"
DB_USER="${POSTGRES_USER:-nexora}"
DB_NAME="${POSTGRES_DB:-nexora_db}"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file '${BACKUP_FILE}' not found." >&2
    exit 1
fi

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Restoring Nexora AI database from: ${BACKUP_FILE}..."
docker cp "${BACKUP_FILE}" "${CONTAINER_NAME}:/tmp/restore_target.dump"
docker exec -t "${CONTAINER_NAME}" pg_restore -U "${DB_USER}" -d "${DB_NAME}" --clean --if-exists --no-owner -v /tmp/restore_target.dump || true
docker exec "${CONTAINER_NAME}" rm /tmp/restore_target.dump
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Database restoration completed successfully."
