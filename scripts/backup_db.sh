#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
CONTAINER_NAME="${DB_CONTAINER:-t4f-postgres-db}"
DB_NAME="${POSTGRES_DB:-t4f_global}"
DB_USER="${POSTGRES_USER:-t4f_app}"
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "==> Creating backup of database '${DB_NAME}' from container '${CONTAINER_NAME}'..."
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists | gzip > "$BACKUP_FILE"

echo "==> Backup successfully created at: $BACKUP_FILE"
echo "==> Size: $(du -h "$BACKUP_FILE" | cut -f1)"
