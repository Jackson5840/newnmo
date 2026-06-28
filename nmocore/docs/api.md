# API Reference

All endpoints are served on port **8002**. Responses are JSON. Paginated endpoints return the `NMOApiPage` format described below.

## Pagination

Most list endpoints return paginated responses:

```json
{
  "status": "success",
  "data": [ ... ],
  "page": 1,
  "size": 100,
  "total": 5000,
  "pages": 50
}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `size` | int | 100 | Items per page (max 500) |

---

## Endpoints

### GET /

List all neurons from the neuronview materialized view.

**Parameters:** `page`, `size`

**Response:** Paginated list of `Neuron` objects.

---

### GET /neuron/

Filter neurons by metadata fields. Supports combining multiple filters. Results are cached for 24 hours.

**Basic Filters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `species_name` | string | Species name (e.g., `rat`, `mouse`) |
| `archive_name` | string | Archive/collection name |
| `strain_name` | string | Strain/breed name |
| `staining_name` | string | Staining method |
| `protocol` | string | Protocol type (`in vivo`, `in vitro`, etc.) |
| `reconstruction` | string | Reconstruction software |
| `age` | string | Age classification (`adult`, `young`, etc.) |
| `gender` | string | Gender (`M`, `F`, `NR`) |

**Hierarchical Filters (ltree):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `region1` | string | Brain region level 1 |
| `region2` | string | Brain region level 2 |
| `region3` | string | Brain region level 3 |
| `celltype1` | string | Cell type level 1 |
| `celltype2` | string | Cell type level 2 |
| `celltype3` | string | Cell type level 3 |

**Structural Filters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `domain` | string | Structural domain (`AX`, `BS`, `AP`, `NEU`, `PR`) |
| `completeness` | string | Completeness level (`Incomplete`, `Moderate`, `Complete`) |
| `struct_domain` | string | Structural domain (alternative) |
| `morph_attributes` | string | Morphological attributes |

**Numeric Range Filters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_age` | float | Minimum age value |
| `max_age` | float | Maximum age value |
| `min_weight` | float | Minimum weight value |
| `max_weight` | float | Maximum weight value |
| `min_age_op` | string | Operator for min_age (`>`, `>=`, `<`, `<=`, `=`) |
| `max_age_op` | string | Operator for max_age |
| `min_weight_op` | string | Operator for min_weight |
| `max_weight_op` | string | Operator for max_weight |

**Special Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `random` | int | Return N random neurons instead of filtering |
| `idlistkey` | string | Redis key containing a pre-filtered list of neuron IDs (from `/search` or previous `/neuron/` call) |

**Response:** Paginated list of `Neuron` objects. Also stores the result ID list in Redis under a key returned in headers for chaining with other endpoints.

---

### GET /neuron/n/

Count neurons matching the same filters as `GET /neuron/`.

**Parameters:** Same as `GET /neuron/` (excluding `random`, `page`, `size`).

**Response:**

```json
{
  "count": 1234
}
```

---

### GET /search/{keyword}

Full-text keyword search across neuron metadata using Redis RediSearch. The search index must be built first via `/feedsearch`.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `keyword` | string (path) | Search keyword |

**Response:** Paginated list of matching `Neuron` objects. Stores matched ID list in Redis for use with `idlistkey`.

---

### GET /browse/{field}/{val}

Browse neurons in a 3-level hierarchical tree grouped by metadata fields.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `field` | string (path) | Field to browse by (`species`, `region`, `celltype`, `archive`) |
| `val` | string (path) | Value to filter on |
| `idlistkey` | string (query, optional) | Redis key for pre-filtered neuron ID list |

**Response:** Nested tree structure with three levels of grouping, each containing neuron records.

---

### GET /quickstats/

Summary counts of key entities in the database. Cached for 24 hours.

**Response:**

```json
{
  "species": 100,
  "brain_region": 500,
  "cell_type": 300,
  "archive": 50,
  "neuron": 200000
}
```

---

### GET /measurements/

L-Measure morphological measurements for neurons. Supports filtering.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Neuron name |
| `idlistkey` | string (optional) | Redis key for pre-filtered ID list |

**Response:** Paginated list of `Measurements` objects containing metrics like soma surface, number of stems, bifurcations, branches, dimensions, and more.

---

### GET /pvec/{name}

Persistence vectors for a specific neuron.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string (path) | Neuron name |

**Response:** Paginated list of `Pvec` objects with distance, coefficient array, and scaling factor.

---

### GET /metavals/

Get distinct values for metadata fields. Useful for populating filter dropdowns.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `fields` | list[string] | Field names to get values for (e.g., `species_name`, `archive_name`) |
| `parent` | string (optional) | Parent value for hierarchical filtering |
| `idlistkey` | string (optional) | Redis key for pre-filtered ID list |

Supports hierarchical fields: `region1`, `region2`, `region3`, `celltype1`, `celltype2`, `celltype3`.

**Response:**

```json
[
  {
    "field": "species_name",
    "vals": ["rat", "mouse", "human", ...]
  }
]
```

---

### GET /chartcount/{field}/{cutoff}

Grouped counts for a metadata field, with smaller groups aggregated into "Others". Useful for generating charts.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `field` | string (path) | Field to count by (e.g., `species_name`) |
| `cutoff` | int (path) | Maximum number of groups before aggregating into "Others" |

**Response:** List of `{fieldvalue, count}` objects.

---

### GET /metacount/{field}

Distinct value count for a metadata field, with optional per-value breakdown.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `field` | string (path) | Field to count (e.g., `species_name`) |
| `detail` | bool (query) | If true, include per-value counts |

**Response (detail=false):**

```json
{
  "count": 42
}
```

**Response (detail=true):**

```json
{
  "field": "species_name",
  "totalcount": 42,
  "fieldcounts": [
    {"fieldvalue": "rat", "count": 15000},
    {"fieldvalue": "mouse", "count": 12000},
    ...
  ]
}
```

---

### GET /getzipped/

Download one or more neuron SWC files as a zip archive.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `names` | list[string] | Neuron names to download |
| `aux` | bool (optional) | Include auxiliary files |

**Response:** Streaming zip file download.

---

### GET /feedsearch

Build (or rebuild) the Redis full-text search index from the database. Must be called before `/search` will work.

**Response:** Status message.

---

### GET /clear

Flush all keys from the Redis cache.

**Response:** Status message.

---

## Shopping Cart

The cart allows users to accumulate neurons across multiple browsing/search sessions, then download them as a ZIP archive. Cart state is stored in Redis with a 24-hour TTL. See [Redis documentation](redis.md) for details on the underlying data model.

### POST /cart/

Create a new empty cart. Returns a `cart_token` (UUID) that must be passed to all subsequent cart operations.

**Response:**

```json
{
  "status": "success",
  "cart_token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "count": 0
}
```

---

### GET /cart/{cart_token}

View the contents of a cart.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `cart_token` | string (path) | Cart token from `POST /cart/` |

**Response:**

```json
{
  "status": "success",
  "cart_token": "a1b2c3d4-...",
  "count": 3,
  "names": ["cnic_001", "cnic_002", "cnic_003"]
}
```

**Errors:** 404 if cart not found or expired.

---

### POST /cart/{cart_token}/add

Add neurons to the cart. Neurons can be specified by name or by an `idlistkey` from a previous search/filter operation. Both can be provided simultaneously.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `cart_token` | string (path) | Cart token |

**Request body (JSON):**

| Field | Type | Description |
| --- | --- | --- |
| `names` | list[string] (optional) | Neuron names to add (validated against DB) |
| `idlistkey` | string (optional) | Redis key from a previous `/neuron/` or `/search/` result |

At least one of `names` or `idlistkey` must be provided.

**Response:**

```json
{
  "status": "success",
  "cart_token": "a1b2c3d4-...",
  "count": 150,
  "warning": "Cart has 1050 neurons, which exceeds the recommended limit of 1000",
  "invalid_names": ["nonexistent_neuron"]
}
```

- `warning` is included when the cart exceeds the soft limit (default 1000, configurable via `CART_SOFT_LIMIT`).
- `invalid_names` lists any requested names not found in the database.
- Duplicate names are silently deduplicated (Redis Sets).

**Errors:**
- 400 if neither `names` nor `idlistkey` provided
- 400 if adding would exceed the hard limit (default 5000, configurable via `CART_HARD_LIMIT`)
- 404 if cart not found or expired
- 404 if `idlistkey` not found or expired

---

### POST /cart/{cart_token}/remove

Remove neurons from the cart by name.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `cart_token` | string (path) | Cart token |

**Request body (JSON):**

| Field | Type | Description |
| --- | --- | --- |
| `names` | list[string] | Neuron names to remove |

**Response:**

```json
{
  "status": "success",
  "cart_token": "a1b2c3d4-...",
  "count": 2
}
```

**Errors:** 404 if cart not found or expired.

---

### DELETE /cart/{cart_token}

Delete a cart and all its contents.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `cart_token` | string (path) | Cart token |

**Response:**

```json
{
  "status": "success"
}
```

**Errors:** 404 if cart not found or expired.

---

### GET /cart/{cart_token}/download

Download all neurons in the cart as a ZIP archive of SWC files.

**Parameters:**

| Parameter | Type | Description |
| --- | --- | --- |
| `cart_token` | string (path) | Cart token |
| `aux` | bool (query, optional) | Include auxiliary files (source version, standardization logs). Default: false |

**Response:** Streaming ZIP file with `Content-Disposition` header.

The ZIP contains one folder per archive, with a `CNG version` subfolder containing the `.CNG.swc` files. If `aux=true`, additional subfolders contain source files, remaining issues, and standardization logs.

**Errors:**
- 400 if cart is empty
- 404 if cart not found or expired

---

## Data Models

### Neuron

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Neuron ID |
| `name` | string | Neuron name |
| `age` | string | Age classification |
| `age_scale` | string | Age scale (D/M/Y) |
| `gender` | string | Gender |
| `region_array` | JSON | Brain regions as JSON array |
| `region_path` | string | Brain region ltree path |
| `celltype_array` | JSON | Cell types as JSON array |
| `celltype_path` | string | Cell type ltree path |
| `archive_name` | string | Archive name |
| `species_name` | string | Species name |
| `strain_name` | string | Strain name |
| `staining_name` | string | Staining method |
| `protocol` | string | Experimental protocol |
| `reconstruction` | string | Reconstruction software |
| `min_age` | float | Minimum age |
| `max_age` | float | Maximum age |
| `min_weight` | float | Minimum weight |
| `max_weight` | float | Maximum weight |
| `depositiondate` | date | Deposition date |
| `uploaddate` | date | Upload date |
| `publication_journal` | string | Journal name |
| `publication_title` | string | Publication title |
| `publication_pmid` | string | PubMed ID |
| `publication_doi` | string | DOI |
| `expcond_name` | string | Experimental condition |
| `magnification` | float | Magnification |
| `objective` | string | Objective type |
| `originalformat_name` | string | Original file format |
| `slicing_direction` | string | Slicing direction |
| `slicingthickness` | float | Slice thickness |
| `shrinkage` | string | Shrinkage status |
| `shrinkagevalues` | JSON | Shrinkage correction values |
| `structural_domain` | JSON | Array of domain/completeness/morphology attributes |
| `png_url` | string | URL to neuron image |
| `note` | string | Notes |
| `url_reference` | string | External reference URL |

### Measurements

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Record ID |
| `name` | string | Neuron name |
| `soma_surface` | float | Soma surface area |
| `n_stems` | float | Number of stems |
| `n_bifs` | float | Number of bifurcations |
| `n_branch` | float | Number of branches |
| `width` | float | Width |
| `height` | float | Height |
| `depth` | float | Depth |
| `diameter` | float | Diameter |
| `length` | float | Total length |
| `surface` | float | Surface area |
| `volume` | float | Volume |
| `eucdistance` | float | Euclidean distance |
| `pathdistance` | float | Path distance |
| `branch_order` | float | Branch order |
| `contraction` | float | Contraction |
| `fragmentation` | float | Fragmentation |
| `partition_asymmetry` | float | Partition asymmetry |
| `pk_classic` | float | Pk classic |
| `bif_ampl_local` | float | Local bifurcation amplitude |
| `bif_ampl_remote` | float | Remote bifurcation amplitude |
| `fractal_dim` | float | Fractal dimension |

### Pvec

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Record ID |
| `name` | string | Neuron name |
| `distance` | float | Distance |
| `coeffarray` | JSON | Coefficient array |
| `sfactor` | float | Scaling factor |
