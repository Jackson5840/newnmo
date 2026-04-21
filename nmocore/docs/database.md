# Database Schema

NMOCore uses PostgreSQL 18 with the **ltree** extension for hierarchical brain region and cell type paths. The full schema is defined in `db/dbschema.sql`.

## Entity Relationship Overview

```
species ←── strain ←── neuron ──→ archive
                         │
                         ├──→ region        (ltree hierarchy)
                         ├──→ celltype      (ltree hierarchy)
                         ├──→ publication
                         ├──→ expcond
                         ├──→ measurements  (summary)
                         │
                         ├──← neuron_structure ──→ measurements
                         ├──← neuron_segment
                         └──← pvec
```

Key: `A ←── B` means B has a foreign key referencing A.

## Custom Enum Types

| Type | Values |
|------|--------|
| `age_type` | adult, aged, embryonic, fetus, infant, larval, neonatal, not reported, old, tadpole, young, young adult |
| `age_scale_type` | D, M, Y, Not reported |
| `gender_type` | F, H, M, M/F, NR, Not reported, Not applicable |
| `objective_type` | dry, electron microscopy, glycerin, multiple, oil, water, water or oil, IR-coated dipping intravital |
| `protocol_type` | culture, ex vivo, in ovo, in utero, in vitro, in vivo, Not reported |
| `slicing_direction_type` | coronal, cross section, custom, flattened, horizontal, multiple, near-coronal, not applicable, oblique coronal, oblique horizontal, parasagittal, sagittal, transverse, whole mount, ... |
| `shrinkage_type` | reported and corrected, reported and not corrected, not applicable |
| `completeness_type` | Incomplete, Moderate, Complete |
| `domain_type` | AP (apical), BS (basal/dendrite), AX (axon), NEU (neurite), PR (process) |
| `status_type` | ready, read, error, ingested, partial, warning, public |
| `exportstatus` | ready, success, warning, error |

## Tables

### neuron

Main table storing neuron records.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Neuron ID |
| `name` | varchar(500) | Neuron name (unique) |
| `archive_id` | int (FK) | Archive reference |
| `region_id` | int (FK) | Brain region reference |
| `celltype_id` | int (FK) | Cell type reference |
| `strain_id` | int (FK) | Strain reference (links to species) |
| `publication_id` | int (FK) | Publication reference |
| `expcond_id` | int (FK) | Experimental condition |
| `summary_meas_id` | int (FK) | Summary measurements |
| `age` | age_type | Age classification |
| `age_scale` | age_scale_type | Age scale |
| `gender` | gender_type | Gender |
| `min_age` | double | Minimum age value |
| `max_age` | double | Maximum age value |
| `min_weight` | double | Minimum weight |
| `max_weight` | double | Maximum weight |
| `has_soma` | bool | Whether neuron includes soma |
| `depositiondate` | date | Date deposited |
| `uploaddate` | date | Date uploaded |
| `magnification` | double | Imaging magnification |
| `reconstruction` | varchar(500) | Reconstruction software |
| `note` | text | Notes |
| `url_reference` | text | External reference URL |
| `png_url` | varchar(1000) | Neuron image URL |

### archive

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Archive ID |
| `name` | varchar(500) | Archive name (unique) |
| `url` | varchar(1000) | Archive URL |

### species

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Species ID |
| `name` | varchar(500) | Species name (unique) |

### strain

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Strain ID |
| `name` | varchar(500) | Strain name |
| `species_id` | int (FK) | Species reference |

### region

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Region ID |
| `name` | varchar(500) | Region name (unique) |
| `path` | ltree | Hierarchical path (e.g., `brain.cortex.layer5`) |

### celltype

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Cell type ID |
| `name` | varchar(500) | Cell type name (unique) |
| `path` | ltree | Hierarchical path |

### publication

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Publication ID |
| `pmid` | varchar(500) | PubMed ID |
| `doi` | varchar(500) | DOI |
| `year` | int | Publication year |
| `journal` | varchar(1000) | Journal name |
| `title` | text | Paper title |
| `first_author` | varchar(500) | First author |
| `last_author` | varchar(500) | Last author |
| `abstract` | text | Abstract |
| `url` | varchar(1000) | Publication URL |

### measurements

L-Measure morphological metrics.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Measurement ID |
| `soma_surface` | double | Soma surface area |
| `n_stems` | double | Number of stems |
| `n_bifs` | double | Number of bifurcations |
| `n_branch` | double | Number of branches |
| `width` | double | Neuron width |
| `height` | double | Neuron height |
| `depth` | double | Neuron depth |
| `diameter` | double | Diameter |
| `length` | double | Total length |
| `surface` | double | Surface area |
| `volume` | double | Volume |
| `eucdistance` | double | Euclidean distance |
| `pathdistance` | double | Path distance |
| `branch_order` | double | Branch order |
| `contraction` | double | Contraction |
| `fragmentation` | double | Fragmentation |
| `partition_asymmetry` | double | Partition asymmetry |
| `pk_classic` | double | Pk classic |
| `bif_ampl_local` | double | Local bifurcation amplitude |
| `bif_ampl_remote` | double | Remote bifurcation amplitude |
| `fractal_dim` | double | Fractal dimension |

### neuron_structure

Links neurons to per-domain measurements with completeness info.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Record ID |
| `neuron_id` | int (FK) | Neuron reference |
| `measurements_id` | int (FK) | Measurements for this domain |
| `completeness` | completeness_type | Completeness level |
| `domain` | domain_type | Structural domain (AX, BS, AP, etc.) |
| `morph_attributes` | varchar(500) | Morphological attributes |

### neuron_segment

3D morphology segment data for neurons.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Segment ID |
| `neuron_id` | int (FK) | Neuron reference |
| `radius` | double | Segment radius |
| `x` | double | X coordinate |
| `y` | double | Y coordinate |
| `z` | double | Z coordinate |
| `type` | int | Segment type |
| `path` | ltree | Hierarchical path in tree |

### pvec

Persistence vectors for topological analysis.

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial (PK) | Record ID |
| `neuron_id` | int (FK) | Neuron reference |
| `distance` | double | Distance metric |
| `coeffs` | double[] | Coefficient array |
| `sfactor` | double | Scaling factor |

### Other Tables

| Table | Purpose |
|-------|---------|
| `expcond` | Experimental conditions (id, name) |
| `staining` | Staining methods (id, name) |
| `originalformat` | Original file formats (id, name, format_type) |
| `shrinkagevalue` | Shrinkage correction values |
| `ingestion` | Data import tracking (neuron_id, status, message) |
| `ingested_archives` | Archive import tracking |
| `export` | Export tracking (neuron_id, status, message) |
| `duplicateactions` | Duplicate resolution actions |
| `version` | Database version (major, minor, patch) |
| `pubversion` | Publication version |
| `acknowledgement` | Acknowledgements |

## Materialized Views

Views are created `WITH NO DATA` and must be refreshed after data import.

### neuronview

Primary view for the API. Joins neuron with all related tables and aggregates structural domains as JSON.

**Key joins:** neuron + archive + region + celltype + strain + species + publication + expcond + staining + originalformat + shrinkagevalue + neuron_structure

### browseview

Flattened view for browsing and charting. Contains one row per neuron with denormalized names.

**Columns:** neuron_id, neuron_name, region_name, celltype_name, archive_name, species_name, png_url

### measurementsview

Neuron names joined with their summary measurements.

### pvecview

Neuron names joined with persistence vector data. Converts the `coeffs` array to a JSON `coeffarray`.

### Refreshing Views

After importing data, refresh all materialized views:

```sql
REFRESH MATERIALIZED VIEW neuronview;
REFRESH MATERIALIZED VIEW browseview;
REFRESH MATERIALIZED VIEW measurementsview;
REFRESH MATERIALIZED VIEW pvecview;
```

## Stored Procedures

### ingest_region(reg_names text[], a_region_path varchar)

Inserts a brain region with its ltree path, automatically creating ancestor regions as needed.

### ingest_celltype(celltype_names text[], a_celltype_path varchar)

Inserts a cell type with its ltree path, automatically creating ancestor cell types as needed.

### ingest_data(...)

Main data ingestion procedure (31 parameters). Creates or finds all related entities (archive, species, strain, publication, experimental condition, etc.) and inserts a neuron record with all relationships. Updates the ingestion tracking table on completion.

## Indexes

The schema creates indexes on:

- Foreign key columns (archive_id, region_id, celltype_id, strain_id, etc.)
- ltree path columns (region.path, celltype.path) with GiST indexes
- Name columns with unique constraints
- neuron_segment spatial columns
