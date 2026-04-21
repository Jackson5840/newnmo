# newnmo

A modernised, containerised deployment of the [NeuroMorpho.Org](https://neuromorpho.org)
stack (FastAPI backend + Pug/SCSS/JS frontend + PostgreSQL + Redis Stack).

Two flavours:

- **Multi-container (`docker-compose.yml`)** — recommended. One container per service.
- **All-in-one (`Dockerfile`)** — every service inside one image, supervised by `supervisord`.

## Quick start (multi-container)

```bash
# 1. Clone
git clone <your-fork-url> newnmo
cd newnmo

# 2. Fetch the database dump (NOT included in the repo, see below)
#    Put it here:  nmocore/pglocdump.sql

# 3. Optional: copy and edit secrets
cp .env.example .env       # CHANGE POSTGRES_PASSWORD for anything non-local!

# 4. Build and launch
docker compose up -d --build

# 5. Wait ~1 minute for first-run DB restore, then open:
#    UI   :  http://localhost:8080
#    API  :  http://localhost:8080/api/
#    Docs :  http://localhost:8080/api/docs
```

### Getting the database dump

`nmocore/pglocdump.sql` (~22 MB, PostgreSQL 16 dump with schema + ~10k neurons) is
**not committed** to this repository to keep clones lightweight.

Option A — copy from an existing deployment:

```bash
# on a host that already has the DB running
docker compose exec db pg_dump -U nmo nmo > pglocdump.sql
scp pglocdump.sql user@newhost:~/newnmo/nmocore/
```

Option B — download a shared copy (internal link / release asset — fill in for
your fork).

Option C — start empty: skip step 2 and the DB comes up with schema only. You
can then ingest data through the backend's import scripts.

## Service layout (compose mode)

| Container         | Image                              | Purpose                           |
|-------------------|------------------------------------|-----------------------------------|
| `nmo-db-1`        | `postgres:16`                      | data store + `ltree` extension    |
| `nmo-cache-1`     | `redis/redis-stack-server:latest`  | RediSearch index + response cache |
| `nmo-nmocore-1`   | built from `nmocore/Dockerfile`    | FastAPI (uvicorn)                 |
| `nmo-nmoui-1`     | built from `nmoui/Dockerfile`      | nginx serving the built frontend  |
| `nmo-nmoui-watcher-1` *(dev only)* | `node:16-bullseye`      | auto-rebuilds UI on source change |

The first-run DB restore is driven by `db-init/*.sh` which load
`nmocore/pglocdump.sql` and then create/refresh materialised views that newer
backend code expects.

## Development (hot reload)

`docker-compose.override.yml` is picked up automatically and enables:

- **Backend**: `uvicorn --reload` watches `nmocore/` — save a `.py` and the
  API reloads in ~1 s.
- **Frontend**: the `nmoui-watcher` container runs `scripts/sb-watch.js` and
  rebuilds `dist/` on any change under `nmoui/src/`. nginx serves the shared
  volume, so you just refresh the browser.

Edit sources in `nmoui/src/` (Pug / SCSS / JS) or `nmocore/` — never the
generated `dist/` or files inside running containers.

To opt out of hot reload (production behaviour):

```bash
docker compose -f docker-compose.yml up -d --build
```

## Configuration

| Variable            | Default  | Purpose                               |
|---------------------|----------|---------------------------------------|
| `POSTGRES_USER`     | `nmo`    | DB user                               |
| `POSTGRES_PASSWORD` | `nmo`    | **Change this for any public host.**  |
| `POSTGRES_DB`       | `nmo`    | DB name                               |
| `UI_PORT`           | `8080`   | host port for the UI                  |
| `DB_PORT`           | `5432`   | host port for Postgres (optional)     |

Build-time:

| Arg            | Default | Purpose                                               |
|----------------|---------|-------------------------------------------------------|
| `API_BASE_URL` | `/api`  | Replaces `apiurlbase` in `nmoui/src/js/base.js`       |

## Common operations

```bash
# Logs
docker compose logs -f nmocore
docker compose logs -f nmoui-watcher

# psql shell
docker compose exec db psql -U nmo -d nmo

# Reset everything (DB + Redis + UI build)
docker compose down -v

# Refresh RediSearch index (after bulk DB changes)
curl http://localhost:8080/api/feedsearch
```

## Directory layout

```
newnmo/
├── docker-compose.yml              # production topology
├── docker-compose.override.yml     # dev overrides (hot reload)
├── Dockerfile                      # all-in-one image (alternative)
├── entrypoint.sh · supervisord.conf · nginx.conf   # for all-in-one
├── .env.example
├── db-init/                        # first-run Postgres init scripts
│   ├── 10-restore.sh               #   load pglocdump.sql
│   └── 20-missing-views.sh         #   patch newer matviews
├── nmocore/                        # FastAPI backend
│   ├── app.py  requirements.txt
│   ├── nmo/    db/
│   └── pglocdump.sql  (NOT in git, fetch separately)
└── nmoui/                          # Pug/SCSS/JS frontend
    ├── package.json  scripts/
    └── src/                        # <-- edit frontend here
```

## Known limitations / TODO

- Backend uses legacy `str.format()` to build SQL in many places. Any public
  deployment must parameterise these queries first.
- `pglocdump.sql` predates some materialised views; `db-init/20-missing-views.sh`
  patches them at restore time.
- `paramiko` / `mysql-connector-python` are only used by the one-shot
  `import_mysql.py` script and could be split off.
- Node 16 is EOL; upgrade path to Node 20 pending.

See the maintainer notes / issue tracker for more.
