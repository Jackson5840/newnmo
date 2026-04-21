# NMOCore

REST API for [NeuroMorpho.Org](https://neuromorpho.org), serving neuron morphology metadata from a PostgreSQL database. Built with FastAPI, PostgreSQL (with ltree extension for hierarchical data), and Redis (for full-text search and caching).

## Quick Start

1. Create a `.env` file with your database credentials:

```env
POSTGRES_USER=nmo
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=nmo
```

2. Build and start all services:

```bash
docker compose up -d --build
```

3. The API is available at `http://localhost:8002`.

4. Build the search index (required for `/search` to work):

```
GET http://localhost:8002/feedsearch
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| **nmocore** | 8002 | FastAPI application |
| **db** | 5432 | PostgreSQL 18 with ltree |
| **cache** | internal | Redis Stack (search + caching) |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | List all neurons (paginated) |
| `GET /neuron/` | Filter neurons by species, region, cell type, and more |
| `GET /neuron/n/` | Count neurons matching filters |
| `GET /search/{keyword}` | Full-text keyword search |
| `GET /browse/{field}/{val}` | Hierarchical browse tree |
| `GET /quickstats/` | Summary counts (species, regions, cell types, archives, neurons) |
| `GET /measurements/` | L-Measure morphological measurements |
| `GET /pvec/{name}` | Persistence vectors for a neuron |
| `GET /metavals/` | Distinct values for metadata fields |
| `GET /chartcount/{field}/{cutoff}` | Grouped counts for charting |
| `GET /metacount/{field}` | Distinct count and breakdown for a field |
| `GET /getzipped/` | Download neuron SWC files as a zip archive |

See [docs/api.md](docs/api.md) for full endpoint documentation with parameters and examples.

## Project Structure

```
nmocore/
├── app.py                  # FastAPI application and all routes
├── Dockerfile              # API container image
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
├── nmo/
│   ├── cfg.py              # Configuration (environment variables)
│   ├── dbmodel.py          # SQLAlchemy tables and Pydantic models
│   └── com.py              # Database utility functions
├── db/
│   ├── Dockerfile          # PostgreSQL container image
│   └── dbschema.sql        # Full database schema
├── tests/
│   └── test_endpoints.py   # Endpoint smoke tests
└── docs/                   # Documentation
```

## Documentation

- [API Reference](docs/api.md) -- endpoints, parameters, and response formats
- [Database Schema](docs/database.md) -- tables, views, types, and relationships
- [Architecture](docs/architecture.md) -- system design, caching, and search
- [Deployment](docs/deployment.md) -- Docker setup, configuration, and operations

## Running Tests

```bash
python3 -m pytest tests/ -v
```

Tests run against a live instance at `http://localhost:8002`.

## License

NeuroMorpho.Org -- George Mason University
