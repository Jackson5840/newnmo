# Architecture

## System Overview

```
                  ┌─────────────┐
  Client ────────→│   FastAPI    │
  (port 8002)     │   (app.py)  │
                  └──┬───────┬──┘
                     │       │
              ┌──────┘       └──────┐
              ▼                     ▼
    ┌──────────────┐      ┌──────────────┐
    │  PostgreSQL   │      │    Redis     │
    │  (port 5432)  │      │   Stack      │
    │  + ltree      │      │  (internal)  │
    └──────────────┘      └──────────────┘
```

The API layer (`app.py`) handles all HTTP requests, translates them into database queries or Redis operations, and returns paginated JSON responses.

## Source Code Layout

| Module | Responsibility |
|--------|---------------|
| `app.py` | Route definitions, request handling, caching logic, pagination |
| `nmo/cfg.py` | Configuration from environment variables |
| `nmo/dbmodel.py` | SQLAlchemy table mappings and Pydantic response models |
| `nmo/com.py` | Direct psycopg2 database operations and utility functions |

## Request Flow

1. Client sends HTTP GET request
2. FastAPI route handler checks Redis cache (hash of query parameters as key)
3. **Cache hit:** deserialize and return cached response
4. **Cache miss:** build SQLAlchemy query or raw SQL, execute against PostgreSQL
5. Serialize result, store in Redis with 24-hour TTL
6. Return paginated JSON response

## Database Access

Two database access patterns are used:

### SQLAlchemy ORM (primary)

Used for most API endpoints. Queries are built against materialized view table objects defined in `nmo/dbmodel.py`. Session management uses FastAPI's dependency injection:

```python
@app.get("/")
def root(db: Session = Depends(get_db)):
    q = db.query(mdl.t_neuronview)
    return paginate(q)
```

### Direct psycopg2 (secondary)

Used in `nmo/com.py` for operations that need raw SQL, such as:
- Data ingestion via stored procedures
- Complex queries with ltree operators
- Bulk data retrieval for search indexing

The `@pgconnect` decorator manages connections automatically.

## Caching Strategy

Redis serves two purposes: response caching and full-text search.

### Response Cache

- **Key generation:** MD5-style hash of path parameters + query parameters
- **TTL:** 86400 seconds (24 hours)
- **Serialization:** `json.dumps()` for simple data, `pickle.dumps()` for complex objects
- **Invalidation:** `GET /clear` flushes all keys

### ID List Caching

Search and filter endpoints store result ID lists in Redis for cross-endpoint chaining:

1. `GET /search/cortex` returns neurons and stores matching IDs in Redis under a generated key
2. `GET /neuron/?idlistkey=<key>&species_name=rat` retrieves the ID list and adds further filters
3. This allows combining full-text search with metadata filtering

ID lists are serialized with `pickle` and stored with a 500,000-second TTL.

## Full-Text Search

Search is implemented using Redis Stack's RediSearch module:

1. **Index building** (`GET /feedsearch`): reads all neuron metadata from PostgreSQL, concatenates text fields with punctuation removed, and creates a RediSearch index
2. **Searching** (`GET /search/{keyword}`): queries the RediSearch index with `FT.SEARCH`, returns matching neuron IDs
3. The search index must be explicitly rebuilt when data changes

## Pagination

Two pagination functions handle different data sources:

| Function | Input | Use Case |
|----------|-------|----------|
| `paginate()` | SQLAlchemy Query object | Database queries (most endpoints) |
| `nosqlpag()` | Python list | Pre-computed results (random neurons, cached data) |

Both return the same `NMOApiPage` response format. The `add_pagination(app)` call at the end of `app.py` wires pagination into FastAPI.

## Hierarchical Data (ltree)

Brain regions and cell types use PostgreSQL's ltree extension for tree-structured data:

- Paths are dot-separated: `brain.cortex.layer5`
- Ancestor queries use the `@>` operator: `path @> 'brain.cortex'`
- Descendant queries use the `<@` operator
- The browse endpoint walks the hierarchy to build nested tree responses
- Stored procedures (`ingest_region`, `ingest_celltype`) automatically create ancestor nodes

## Error Handling

- FastAPI's `RequestValidationError` is caught and returns `{"errors": [...], "status": "error"}`
- Database errors propagate as HTTP 500 responses
- Redis connection failures fall through to database queries (no cache)

## CORS

Allowed origins:
- `http://localhost:3000`
- `http://localhost:3002`
- `http://localhost`
- `http://cng-nmo-main.orc.gmu.edu`
