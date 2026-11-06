#!/usr/bin/env bash
set -euo pipefail

if [ -z "${1:-}" ]; then
    echo "Usage: $0 <path_to_backup.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    exit 1
fi

CONTAINER_NAME="${DB_CONTAINER:-t4f-postgres-db}"
DB_NAME="${POSTGRES_DB:-t4f_global}"
DB_USER="${POSTGRES_USER:-t4f_app}"

echo "==> Restoring database '${DB_NAME}' from '$BACKUP_FILE' into container '${CONTAINER_NAME}'..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME"

echo "==> Database restore completed successfully."
