#!/bin/bash
# Restore pglocdump.sql into the freshly-created database.
# Runs with ON_ERROR_STOP=0 so benign errors (role already exists,
# database already exists, etc.) don't abort the whole restore.
set -u

DUMP=/docker-entrypoint-initdb.d/pglocdump.sql

if [ ! -f "$DUMP" ]; then
    echo "[restore] No dump found at $DUMP, skipping."
    exit 0
fi

echo "[restore] Loading $DUMP into PostgreSQL..."
psql -v ON_ERROR_STOP=0 \
     --username "$POSTGRES_USER" \
     --dbname postgres \
     -f "$DUMP" \
     2> >(grep -vE "already exists|skipping" >&2) || true

echo "[restore] Done."
