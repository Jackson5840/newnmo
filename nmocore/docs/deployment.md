# Deployment

## Prerequisites

- Docker and Docker Compose
- Sufficient disk space for the PostgreSQL data volume

## Configuration

All configuration is done through environment variables, stored in a `.env` file at the project root. Docker Compose loads this file automatically.

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | PostgreSQL username | `nmo` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `secretpassword` |
| `POSTGRES_DB` | Database name | `nmo` |

### MySQL Import Variables

These are used by `import_mysql.py` to migrate data from an existing NeuroMorpho.Org MySQL database into PostgreSQL.

| Variable | Default | Description |
|----------|---------|-------------|
| `MYSQL_HOST` | `localhost` | MySQL server hostname |
| `MYSQL_USER` | `root` | MySQL username |
| `MYSQL_PASSWORD` | *(empty)* | MySQL password |
| `MYSQL_DB` | `nmo` | MySQL database name |

### Optional / Internal Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `db` | PostgreSQL hostname (set by Docker networking) |
| `REDIS_HOST` | `cache` | Redis hostname (set by Docker networking) |

### Example .env

```env
POSTGRES_USER=nmo
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=nmo

# Only needed for MySQL import
MYSQL_HOST=mysql.example.com
MYSQL_USER=root
MYSQL_PASSWORD=mysqlpassword
MYSQL_DB=nmo
```

## Starting the Services

```bash
docker compose up -d --build
```

This builds and starts three containers:

| Container | Image | Port |
|-----------|-------|------|
| db | Custom (PostgreSQL + schema) | 5432 |
| nmocore | Custom (Ubuntu + Python + FastAPI) | 8002 |
| cache | redis/redis-stack-server | internal only |

### First Start

On the first start, PostgreSQL automatically:
1. Creates the database and user from environment variables
2. Runs `db/dbschema.sql` to create the full schema (types, tables, views, indexes, etc.)
3. Refreshes materialized views (they will be empty until data is imported)

### Subsequent Starts

PostgreSQL data persists in `/data/db/nmopgdata`. The schema is only executed on first initialization.

## Importing Data

### From a PostgreSQL dump

```bash
docker exec -i nmocore-db-1 psql -U nmo nmo < your_dump.sql
```

### From MySQL (migration)

The `import_mysql.py` script reads from the legacy NeuroMorpho.Org MySQL database and inserts data into PostgreSQL using the `ingest_data` stored procedure. Set the `MYSQL_*` variables in `.env`, then:

```bash
# Import all neurons
python import_mysql.py

# Import first 10 neurons (for testing)
python import_mysql.py --limit 10

# Dry run (no writes)
python import_mysql.py --dry-run --limit 5

# Import a specific neuron by MySQL ID
python import_mysql.py --neuron-id 12345
```

Progress is logged to `import_mysql.log`.

### After importing

Refresh all materialized views:

```bash
docker exec nmocore-db-1 psql -U nmo nmo -c "
  REFRESH MATERIALIZED VIEW neuronview;
  REFRESH MATERIALIZED VIEW browseview;
  REFRESH MATERIALIZED VIEW measurementsview;
  REFRESH MATERIALIZED VIEW pvecview;
"
```

Then build the search index:

```
curl http://localhost:8002/feedsearch
```

## Resetting the Database

To wipe the database and reinitialize from the schema:

```bash
docker compose down
sudo rm -rf /data/db/nmopgdata
docker compose up -d --build
```

## Service Details

### PostgreSQL (db)

- Based on the official `postgres` image
- Schema auto-loaded from `db/dbschema.sql` via `/docker-entrypoint-initdb.d/`
- Data volume: `/data/db/nmopgdata` (host) mapped to `/var/lib/postgresql/data/pgdata` (container)
- Port 5432 is exposed for external database access (e.g., pgAdmin, psql)

### FastAPI (nmocore)

- Based on Ubuntu Bionic with Python 3.8
- Runs via uvicorn with `--reload` and debug logging
- Depends on the `db` service (waits for it to start)
- Restarts automatically on failure

### Redis (cache)

- Uses `redis/redis-stack-server` (includes RediSearch module)
- Port is not exposed externally (accessible only within Docker network)
- Configuration:
  - Append-only persistence enabled
  - 12 I/O threads with read threading
  - allkeys-lru eviction policy
  - 4 GB max memory
  - RediSearch max results unlimited (`MAXSEARCHRESULTS -1`)

## Operations

### Checking Service Status

```bash
docker compose ps
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f nmocore
```

### Clearing the Cache

```bash
curl http://localhost:8002/clear
```

### Rebuilding the Search Index

```bash
curl http://localhost:8002/feedsearch
```

### Connecting to the Database

```bash
# Via docker exec
docker exec -it nmocore-db-1 psql -U nmo nmo

# Via external client (port 5432 is exposed)
psql -h localhost -U nmo nmo
```

### Rebuilding Containers

```bash
# Rebuild and restart all
docker compose up -d --build

# Rebuild a specific service
docker compose up -d --build nmocore
```

## Monitoring

### Health Check

A quick way to verify the API is running:

```bash
curl http://localhost:8002/quickstats/
```

This returns counts of species, regions, cell types, archives, and neurons. If the database is empty, all counts will be zero.

### Running Tests

```bash
python3 -m pytest tests/ -v
```

Tests run against `http://localhost:8002` and expect all endpoints to return HTTP 200.
