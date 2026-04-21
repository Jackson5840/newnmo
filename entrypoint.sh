#!/bin/bash
# First-run bootstrap for the all-in-one NMO container.
# - Initialises the PostgreSQL cluster on a fresh volume
# - Creates the nmo user + database + ltree extension
# - Loads dbschema.sql and any SQL dump mounted under /docker-entrypoint-initdb.d/
# - Then execs supervisord (CMD) to run all services
set -euo pipefail

PG_VERSION=14
PG_BIN=/usr/lib/postgresql/${PG_VERSION}/bin
PGDATA=${PGDATA:-/var/lib/postgresql/${PG_VERSION}/main}

mkdir -p /var/log/supervisor /var/lib/redis-stack /var/run/postgresql
chown -R postgres:postgres /var/run/postgresql "$(dirname "$PGDATA")"
chown -R redis:redis /var/lib/redis-stack 2>/dev/null || true

if [ ! -s "${PGDATA}/PG_VERSION" ]; then
    echo "[entrypoint] Initialising PostgreSQL cluster at ${PGDATA}"
    rm -rf "${PGDATA}"
    mkdir -p "${PGDATA}"
    chown -R postgres:postgres "${PGDATA}"
    chmod 700 "${PGDATA}"

    sudo -u postgres "${PG_BIN}/initdb" \
        -D "${PGDATA}" \
        --auth-local=trust --auth-host=md5 \
        --username=postgres --encoding=UTF8

    # Bind only to loopback (the API talks to us via 127.0.0.1)
    {
        echo "listen_addresses = '127.0.0.1'"
        echo "unix_socket_directories = '/var/run/postgresql'"
    } >> "${PGDATA}/postgresql.conf"

    echo "[entrypoint] Starting PostgreSQL temporarily for bootstrap..."
    sudo -u postgres "${PG_BIN}/pg_ctl" -D "${PGDATA}" -l /tmp/pg-bootstrap.log -w start

    sudo -u postgres psql -v ON_ERROR_STOP=1 <<-SQL
        CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}' SUPERUSER;
        CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER};
SQL

    sudo -u postgres psql -v ON_ERROR_STOP=1 -d "${POSTGRES_DB}" \
        -c "CREATE EXTENSION IF NOT EXISTS ltree;"

    if [ -f /app/db/dbschema.sql ]; then
        echo "[entrypoint] Loading /app/db/dbschema.sql..."
        sudo -u postgres psql -v ON_ERROR_STOP=0 \
            -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -h /var/run/postgresql \
            -f /app/db/dbschema.sql || echo "[entrypoint] dbschema load had warnings"
    fi

    # Optional: any *.sql dropped into /docker-entrypoint-initdb.d/ gets loaded.
    shopt -s nullglob
    for f in /docker-entrypoint-initdb.d/*.sql; do
        echo "[entrypoint] Loading ${f}..."
        sudo -u postgres psql -v ON_ERROR_STOP=0 \
            -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -h /var/run/postgresql \
            -f "${f}" || echo "[entrypoint] ${f} had warnings"
    done
    shopt -u nullglob

    sudo -u postgres "${PG_BIN}/pg_ctl" -D "${PGDATA}" -m fast -w stop
    echo "[entrypoint] PostgreSQL bootstrap complete."
else
    echo "[entrypoint] Existing PostgreSQL cluster detected, skipping init."
fi

exec "$@"
