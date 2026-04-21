# syntax=docker/dockerfile:1.6
#
# All-in-one image for NeuroMorpho.Org (nmocore + nmoui + postgres + redis).
#
# This folder is self-contained: `nmocore/` and `nmoui/` live inside it.
# Build context IS this folder. Example:
#   cd newnmo && docker build -t nmo:all .
#
# ============================================================================
# Stage 1 - build the static frontend (Pug/SCSS/JS -> dist/)
# ============================================================================
FROM node:16-bullseye AS uibuild

WORKDIR /ui
COPY nmoui/package.json nmoui/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY nmoui/scripts ./scripts
COPY nmoui/src ./src

# Rewrite the hard-coded API base URL at build time (source is not modified).
ARG API_BASE_URL=/api
RUN sed -i "s|^const apiurlbase = .*|const apiurlbase = '${API_BASE_URL}';|" src/js/base.js \
 && npm run build


# ============================================================================
# Stage 2 - runtime with every service bundled
# ============================================================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=America/New_York \
    LANG=C.UTF-8 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# --- System packages ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg lsb-release wget sudo \
        python3 python3-pip python3-dev libpq-dev libffi-dev build-essential \
        nginx supervisor tzdata locales \
        postgresql-14 postgresql-contrib-14 \
 && curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o /usr/share/keyrings/redis-archive-keyring.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/redis-archive-keyring.gpg] https://packages.redis.io/deb $(lsb_release -cs) main" \
        > /etc/apt/sources.list.d/redis.list \
 && apt-get update && apt-get install -y --no-install-recommends redis-stack-server \
 && rm -rf /var/lib/apt/lists/*

# Drop the auto-created cluster - we initialise it in the entrypoint instead
RUN pg_dropcluster --stop 14 main 2>/dev/null || true \
 && rm -rf /var/lib/postgresql/14/main /etc/postgresql/14/main

# --- Python deps for nmocore -------------------------------------------------
COPY nmocore/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -U pip \
 && pip3 install --no-cache-dir -r /tmp/requirements.txt

# --- Backend source ---------------------------------------------------------
COPY nmocore/nmo /app/nmo
COPY nmocore/app.py /app/app.py
COPY nmocore/db/dbschema.sql /app/db/dbschema.sql

# --- Frontend build artefacts ----------------------------------------------
COPY --from=uibuild /ui/dist /var/www/html

# --- Service configuration --------------------------------------------------
COPY newnmo/nginx.conf /etc/nginx/sites-available/default
COPY newnmo/supervisord.conf /etc/supervisor/conf.d/nmo.conf
COPY newnmo/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
 && mkdir -p /var/log/supervisor /var/lib/redis-stack /docker-entrypoint-initdb.d \
 && chown -R redis:redis /var/lib/redis-stack 2>/dev/null || true

ENV POSTGRES_USER=nmo \
    POSTGRES_PASSWORD=nmo \
    POSTGRES_DB=nmo \
    POSTGRES_HOST=127.0.0.1 \
    REDIS_HOST=127.0.0.1 \
    ROOT_PATH=/api \
    PGDATA=/var/lib/postgresql/14/main

# Persist database + redis data via named volumes (or bind mounts)
VOLUME ["/var/lib/postgresql/14/main", "/var/lib/redis-stack"]

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
