#!/usr/bin/env bash
# ==============================================================================
# Nexora AI - Automated PostgreSQL Backup Script
# ==============================================================================
set -eo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONTAINER_NAME="${PG_CONTAINER:-nexora_postgres}"
DB_USER="${POSTGRES_USER:-nexora}"
DB_NAME="${POSTGRES_DB:-nexora_db}"
BACKUP_FILE="${BACKUP_DIR}/nexora_${DB_NAME}_${TIMESTAMP}.dump"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"

echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Starting Nexora AI database backup..."

if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" -F c -b -v -f "/tmp/nexora_backup_${TIMESTAMP}.dump"
    docker cp "${CONTAINER_NAME}:/tmp/nexora_backup_${TIMESTAMP}.dump" "${BACKUP_FILE}"
    docker exec "${CONTAINER_NAME}" rm "/tmp/nexora_backup_${TIMESTAMP}.dump"
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Backup completed: ${BACKUP_FILE}"
else
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] ERROR: Container '${CONTAINER_NAME}' is not running." >&2
    exit 1
fi

# Apply retention policy
find "${BACKUP_DIR}" -name "nexora_${DB_NAME}_*.dump" -type f -mtime +"${RETENTION_DAYS}" -delete
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] Retention policy applied (Kept last ${RETENTION_DAYS} days)."
