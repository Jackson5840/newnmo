FROM python:3.10-slim-bookworm

ENV TZ=America/New_York \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 libpq-dev gcc build-essential iputils-ping tzdata \
 && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt \
 && pip install --no-cache-dir --upgrade 'psycopg2-binary>=2.9.9'

COPY ./nmo /app/nmo
COPY app.py /app/

EXPOSE 8002
CMD ["uvicorn", "app:app", "--h11-max-incomplete-event-size", "16777216", "--host", "0.0.0.0", "--port", "8002", "--log-level", "info"]
