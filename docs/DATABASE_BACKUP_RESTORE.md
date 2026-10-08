# Nexora AI — Database Backup, Disaster Recovery & Restoration Runbook

---

## 1. Executive Summary & Overview

This runbook defines standard operating procedures (SOP) for the **Nexora AI Relational Database Subsystem** (PostgreSQL in production and SQLite in dev/edge environments). It provides automated backup scripts, point-in-time recovery (PITR) procedures, single-tenant data extraction workflows, and disaster recovery validation checklists.

---

## 2. Quick Reference Command Cheat Sheet

### 2.1 Backup Commands (PostgreSQL in Docker)

```bash
# 1. Immediate compressed PostgreSQL database backup
docker exec -t nexora_postgres pg_dump -U nexora -d nexora_db -F c -b -v -f /tmp/nexora_backup.dump
docker cp nexora_postgres:/tmp/nexora_backup.dump ./backups/nexora_backup_$(date +%Y%m%d_%H%M%S).dump

# 2. Plain SQL text backup (human-readable schema & data)
docker exec -t nexora_postgres pg_dump -U nexora -d nexora_db --clean --if-exists | gzip > ./backups/nexora_backup_$(date +%Y%m%d_%H%M%S).sql.gz

# 3. Schema-only backup (DDL without rows)
docker exec -t nexora_postgres pg_dump -U nexora -d nexora_db --schema-only > ./backups/nexora_schema_$(date +%Y%m%d).sql
```

### 2.2 Restore Commands (PostgreSQL in Docker)

```bash
# 1. Restore from compressed custom-format dump (.dump)
docker cp ./backups/nexora_backup_20261007.dump nexora_postgres:/tmp/restore.dump
docker exec -t nexora_postgres pg_restore -U nexora -d nexora_db --clean --if-exists -v /tmp/restore.dump

# 2. Restore from gzipped SQL file (.sql.gz)
gunzip -c ./backups/nexora_backup_20261007.sql.gz | docker exec -i nexora_postgres psql -U nexora -d nexora_db
```

### 2.3 SQLite Backup Commands (Development / Edge Deployments)

```bash
# Safe live SQLite backup via online VACUUM INTO
sqlite3 nexora.db "VACUUM INTO 'backups/nexora_dev_backup_$(date +%Y%m%d_%H%M%S).db';"
```

---

## 3. Automated Backup Scripts

Nexora AI includes turnkey automated backup scripts for both Unix/Linux and Windows environments.

### 3.1 Linux / macOS Automation Script (`backend/scripts/backup_postgres.sh`)

Location: `backend/scripts/backup_postgres.sh`

```bash
#!/usr/bin/env bash
set -eo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONTAINER_NAME="${PG_CONTAINER:-nexora_postgres}"
DB_USER="${POSTGRES_USER:-nexora}"
DB_NAME="${POSTGRES_DB:-nexora_db}"
BACKUP_FILE="${BACKUP_DIR}/nexora_${DB_NAME}_${TIMESTAMP}.dump"
RETENTION_DAYS=14

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting Nexora AI PostgreSQL backup..."
docker exec -t "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" -F c -b -v -f "/tmp/nexora_backup_${TIMESTAMP}.dump"
docker cp "${CONTAINER_NAME}:/tmp/nexora_backup_${TIMESTAMP}.dump" "${BACKUP_FILE}"
docker exec "${CONTAINER_NAME}" rm "/tmp/nexora_backup_${TIMESTAMP}.dump"

echo "[$(date)] Backup completed successfully: ${BACKUP_FILE} ($(du -h "${BACKUP_FILE}" | cut -f1))"

# Retention policy: Prune backups older than 14 days
find "${BACKUP_DIR}" -name "nexora_${DB_NAME}_*.dump" -type f -mtime +${RETENTION_DAYS} -delete
echo "[$(date)] Pruned backups older than ${RETENTION_DAYS} days."
```

### 3.2 Automated Linux Cron Schedule

To automate daily backups at 02:00 AM UTC with retention management, add the following entry to `crontab -e`:

```cron
# Daily automated Nexora AI PostgreSQL backup at 02:00 AM UTC
0 2 * * * /bin/bash /opt/nexora_ai/backend/scripts/backup_postgres.sh >> /var/log/nexora_backup.log 2>&1
```

---

## 4. Single-Tenant Data Isolation & Export Procedure

To satisfy enterprise GDPR, SOC 2, or customer data offboarding requests, extract single-tenant records without dumping the full multi-tenant database:

```sql
-- Export single tenant datasets, schemas, and alerts into CSV/JSON
COPY (
    SELECT d.id AS dataset_id, d.tenant_id, d.name, d.department, d.row_count, s.kpis_extracted, s.trends_detected
    FROM datasets d
    LEFT JOIN dataset_schemas s ON d.id = s.dataset_id
    WHERE d.tenant_id = 'target_tenant_id'
) TO '/tmp/tenant_export.csv' WITH CSV HEADER;
```

---

## 5. Disaster Recovery (DR) Step-by-Step Restoration Runbook

In the event of database corruption, container failure, or data loss, execute the following 5-step restoration protocol:

### Step 1: Halt Application Traffic
Temporarily scale down backend workers or route API gateway traffic to maintenance mode:
```bash
docker-compose stop backend frontend
```

### Step 2: Verify Target Backup Integrity
```bash
# Verify dump structure without executing
pg_restore -l ./backups/nexora_nexora_db_20261007_020000.dump | head -n 30
```

### Step 3: Recreate Clean Database
```bash
docker exec -it nexora_postgres psql -U nexora -c "DROP DATABASE IF EXISTS nexora_db;"
docker exec -it nexora_postgres psql -U nexora -c "CREATE DATABASE nexora_db WITH OWNER nexora ENCODING 'UTF8';"
```

### Step 4: Execute Restoration
```bash
docker cp ./backups/nexora_nexora_db_20261007_020000.dump nexora_postgres:/tmp/restore_target.dump
docker exec -t nexora_postgres pg_restore -U nexora -d nexora_db --no-owner --role=nexora -v /tmp/restore_target.dump
docker exec nexora_postgres rm /tmp/restore_target.dump
```

### Step 5: Validate Data Integrity & Restart Stack
```bash
# Check table count and user records
docker exec -it nexora_postgres psql -U nexora -d nexora_db -c "\dt"
docker exec -it nexora_postgres psql -U nexora -d nexora_db -c "SELECT count(*) FROM users;"
docker exec -it nexora_postgres psql -U nexora -d nexora_db -c "SELECT count(*) FROM datasets;"

# Restart services
docker-compose up -d

# Verify health endpoint
curl -f http://localhost:8000/health
```

---

## 6. Disaster Recovery Verification Checklist

- [ ] Backup verified with `pg_restore -l`.
- [ ] Database restored without schema migration errors.
- [ ] Multi-tenant data isolation verified across sample tenant IDs.
- [ ] `/health` endpoint reports `"database": {"status": "healthy"}` with $<5\text{ms}$ latency.
- [ ] ChromaDB vector collection sync verified against relational `datasets` table.
- [ ] Redis cache purged via `POST /api/v1/query/cache-clear` to prevent stale queries against restored data.
