#!/usr/bin/env python3
"""
Import neurons from MySQL export_neuron view into PostgreSQL.

Usage:
    python import_mysql.py                         # Import all neurons
    python import_mysql.py --limit 10              # Import first 10 neurons
    python import_mysql.py --dry-run --limit 5     # Dry run, 5 neurons
    python import_mysql.py --neuron-id 12345       # Import specific neuron
"""

import argparse
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

import mysql.connector
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nmo import cfg

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    handlers=[
        logging.FileHandler("import_mysql.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enum mappings  (MySQL value → PostgreSQL enum value)
# ---------------------------------------------------------------------------

AGE_MAP = {
    "Adult": "adult",
    "adult": "adult",
    "Aged": "aged",
    "aged": "aged",
    "Embryonic": "embryonic",
    "embryonic": "embryonic",
    "Fetus": "fetus",
    "fetus": "fetus",
    "Infant": "infant",
    "infant": "infant",
    "Larval": "larval",
    "larval": "larval",
    "Neonatal": "neonatal",
    "neonatal": "neonatal",
    "Old": "old",
    "old": "old",
    "Tadpole": "tadpole",
    "tadpole": "tadpole",
    "Young": "young",
    "young": "young",
    "Young Adult": "young adult",
    "young adult": "young adult",
    "Young adult": "young adult",
    "Not reported": "Not reported",
    "not reported": "not reported",
}

AGE_SCALE_MAP = {
    "Days": "D",
    "days": "D",
    "D": "D",
    "Months": "M",
    "months": "M",
    "M": "M",
    "Years": "Y",
    "years": "Y",
    "Y": "Y",
    "Not reported": "Not reported",
}

GENDER_MAP = {
    "male": "M",
    "Male": "M",
    "M": "M",
    "female": "F",
    "Female": "F",
    "F": "F",
    "hermaphrodite": "H",
    "Hermaphrodite": "H",
    "H": "H",
    "male/female": "M/F",
    "Male/Female": "M/F",
    "M/F": "M/F",
    "Not reported": "Not reported",
    "not reported": "NR",
    "NR": "NR",
    "Not applicable": "Not applicable",
    "not applicable": "Not applicable",
}

OBJECTIVE_MAP = {
    "Dry": "dry",
    "dry": "dry",
    "Electron microscopy": "electron microscopy",
    "electron microscopy": "electron microscopy",
    "Glycerin": "glycerin",
    "glycerin": "glycerin",
    "Multiple": "multiple",
    "multiple": "multiple",
    "Oil": "oil",
    "oil": "oil",
    "Water": "water",
    "water": "water",
    "Water or oil": "water or oil",
    "water or oil": "water or oil",
    "IR-coated dipping intravital": "IR-coated dipping intravital",
    "Not reported": "Not reported",
}

PROTOCOL_MAP = {
    "Culture": "culture",
    "culture": "culture",
    "Ex vivo": "ex vivo",
    "ex vivo": "ex vivo",
    "In ovo": "in ovo",
    "in ovo": "in ovo",
    "In utero": "in utero",
    "in utero": "in utero",
    "In vitro": "in vitro",
    "in vitro": "in vitro",
    "In vivo": "in vivo",
    "in vivo": "in vivo",
    "Not reported": "Not reported",
}

# All valid PostgreSQL slicing_direction_type values
SLICING_DIRECTION_VALUES = {
    "coronal", "cross section", "custom", "flattened", "horizontal",
    "multiple", "near-coronal", "not applicable", "Not reported",
    "oblique coronal", "oblique horizontal",
    "parallel to the cortical surface", "parasagittal",
    "perpendicular to cortical layers", "perpendicular to the long axis",
    "sagittal", "semi-coronal", "semi-horizontal", "tangential",
    "thalamocortical", "transverse", "whole mount",
    "Not applicable", "Sagittal",
}

COMPLETENESS_MAP = {
    "Incomplete": "Incomplete",
    "incomplete": "Incomplete",
    "Moderate": "Moderate",
    "moderate": "Moderate",
    "Complete": "Complete",
    "complete": "Complete",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def cleanstr(astring):
    """Sanitize a string for use in an ltree path segment.

    Mirrors nmo.com.cleanstr: strips leading space, replaces spaces with
    underscores, keeps only alphanumeric and underscore characters.
    """
    if not astring:
        return ""
    if astring[0] == " ":
        astring = astring[1:]
    astring = astring.replace(" ", "_")
    return "".join(
        c for c in astring if c.isalpha() or c.isdigit() or c == "_"
    ).rstrip()


def build_region_path(row):
    """Build region names list and ltree path from MySQL row.

    Returns (names_list, ltree_path_string) or (None, None) if no region data.
    """
    levels = [
        row.get("region1"),
        row.get("region2"),
        row.get("region3"),
        row.get("region3B"),
        row.get("region5"),
    ]
    names = []
    path_parts = []
    for lvl in levels:
        if lvl is None or str(lvl).strip() == "":
            break
        names.append(str(lvl))
        cleaned = cleanstr(str(lvl))
        if not cleaned:
            break
        path_parts.append(cleaned)
    if not names:
        return None, None
    return names, ".".join(path_parts)


def build_celltype_path(row):
    """Build celltype names list and ltree path from MySQL row.

    Returns (names_list, ltree_path_string) or (None, None) if no data.
    """
    levels = [
        row.get("class1"),
        row.get("class2"),
        row.get("class3"),
        row.get("class3B"),
        row.get("class3C"),
    ]
    names = []
    path_parts = []
    for lvl in levels:
        if lvl is None or str(lvl).strip() == "":
            break
        names.append(str(lvl))
        cleaned = cleanstr(str(lvl))
        if not cleaned:
            break
        path_parts.append(cleaned)
    if not names:
        return None, None
    return names, ".".join(path_parts)


def map_shrinkage_type(row):
    """Derive PostgreSQL shrinkage_type enum value from MySQL columns."""
    # Try the explicit shrinkage_type column first
    st = row.get("shrinkage_type")
    if st:
        st_lower = str(st).strip().lower()
        if "not applicable" in st_lower:
            return "Not reported"
        if "reported" in st_lower and "not corrected" in st_lower:
            return "reported and not corrected"
        if "reported" in st_lower and "corrected" in st_lower:
            return "reported and corrected"
        if "not reported" in st_lower:
            return "Not reported"

    # Fall back to deriving from reported/corrected boolean columns
    reported = row.get("shrinkage_reported")
    corrected = row.get("shrinkage_corrected")
    if reported and str(reported).lower() in ("yes", "reported", "1"):
        if corrected and str(corrected).lower() in ("yes", "corrected", "1"):
            return "reported and corrected"
        return "reported and not corrected"
    return "Not reported"


def map_slicing_direction(value):
    """Map MySQL slicing direction to PostgreSQL slicing_direction_type enum."""
    if value is None:
        return "Not reported"
    value = str(value).strip()
    if value in SLICING_DIRECTION_VALUES:
        return value
    # Case-insensitive fallback
    for v in SLICING_DIRECTION_VALUES:
        if v.lower() == value.lower():
            return v
    log.warning("Unknown slicing_direction '%s', using 'Not reported'", value)
    return "Not reported"


def safe_float(val):
    """Convert to float or return None."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_int(val):
    """Convert to int or return None."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def safe_str(val):
    """Convert to stripped string or return None for empty/NULL."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


# ---------------------------------------------------------------------------
# Per-neuron import
# ---------------------------------------------------------------------------


def import_neuron(pg_conn, row, dry_run=False):
    """Import a single neuron from a MySQL row dict into PostgreSQL.

    Returns one of: 'imported', 'skipped', 'error'.
    """
    neuron_name = row["neuron_name"]
    mysql_id = row["neuron_id"]
    cur = pg_conn.cursor()

    # ── 1. Skip check ─────────────────────────────────────────────────────
    cur.execute("SELECT 1 FROM neuron WHERE name = %s", (neuron_name,))
    if cur.fetchone():
        log.info("SKIP  %s (already in PostgreSQL)", neuron_name)
        return "skipped"

    if dry_run:
        log.info("DRY   %s (mysql_id=%s)", neuron_name, mysql_id)
        return "skipped"

    # ── 2. Ingest region ──────────────────────────────────────────────────
    region_names, region_path = build_region_path(row)
    region_id = 0  # 0 tells ingest_data to set region_id = NULL
    if region_names and region_path:
        cur.execute("CALL ingest_region(%s, %s)", (region_names, region_path))
        cur.execute(
            "SELECT id FROM region WHERE path = text2ltree(%s)", (region_path,)
        )
        res = cur.fetchone()
        if res:
            region_id = res[0]

    # ── 3. Ingest celltype ────────────────────────────────────────────────
    ct_names, ct_path = build_celltype_path(row)
    celltype_id = None
    if ct_names and ct_path:
        cur.execute("CALL ingest_celltype(%s, %s)", (ct_names, ct_path))
        cur.execute(
            "SELECT id FROM celltype WHERE path = text2ltree(%s)", (ct_path,)
        )
        res = cur.fetchone()
        if res:
            celltype_id = res[0]

    if celltype_id is None:
        log.error("ERROR %s — could not resolve celltype", neuron_name)
        return "error"

    # ── 4. Insert shrinkage values ────────────────────────────────────────
    shrinkage_value_id = None
    rv = safe_float(row.get("reported_value"))
    rxy = safe_float(row.get("reported_xy"))
    rz = safe_float(row.get("reported_z"))
    cv = safe_float(row.get("corrected_value"))
    cxy = safe_float(row.get("corrected_xy"))
    cz = safe_float(row.get("corrected_z"))
    if any(v is not None for v in (rv, rxy, rz, cv, cxy, cz)):
        cur.execute(
            """INSERT INTO shrinkagevalue
                   (reported_value, reported_xy, reported_z,
                    corrected_value, corrected_xy, corrected_z)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (rv, rxy, rz, cv, cxy, cz),
        )
        shrinkage_value_id = cur.fetchone()[0]

    # ── 5. Map enums ─────────────────────────────────────────────────────
    age = AGE_MAP.get(row.get("age_classification"), "Not reported")
    age_scale = AGE_SCALE_MAP.get(row.get("age_scale"), "Not reported")
    gender = GENDER_MAP.get(row.get("gender"), "Not reported")
    objective = OBJECTIVE_MAP.get(row.get("objective"), "Not reported")
    protocol = PROTOCOL_MAP.get(row.get("protocol"), "Not reported")
    slicing_dir = map_slicing_direction(row.get("slice_direction"))
    shrinkage = map_shrinkage_type(row)

    # ── Scalar fields ────────────────────────────────────────────────────
    archive_name = safe_str(row.get("archive")) or "Unknown"
    archive_url = safe_str(row.get("archive_URL")) or ""
    species = safe_str(row.get("species")) or "Not reported"
    strain = safe_str(row.get("strain")) or "Not reported"
    expcond = safe_str(row.get("expercond")) or "Not reported"
    stain = safe_str(row.get("stain")) or "Not reported"
    magnification = safe_str(row.get("magnification"))
    orig_format = safe_str(row.get("format")) or "Not reported"
    thickness = safe_str(row.get("thickness"))
    reconstruction = safe_str(row.get("reconstruction"))
    url_reference = safe_str(row.get("URL_reference"))
    note = safe_str(row.get("note"))
    max_age = safe_float(row.get("max_age"))
    min_age = safe_float(row.get("min_age"))
    min_weight = safe_float(row.get("min_weight"))
    max_weight = safe_float(row.get("max_weight"))

    pmid = safe_int(row.get("pmid"))
    if pmid is None:
        pmid = -1
    doi = safe_str(row.get("doi")) or ""

    dep_date = row.get("deposition_date")
    upl_date = row.get("upload_date")
    if dep_date is None:
        dep_date = datetime.now().date()
    if upl_date is None:
        upl_date = datetime.now().date()

    # ── 6. Insert ingestion row (required before ingest_data) ─────────
    cur.execute(
        """INSERT INTO ingestion (neuron_name, archive, status, message)
           VALUES (%s, %s, 'ready', 'MySQL import')""",
        (neuron_name, archive_name),
    )

    # ── 7. Call ingest_data ──────────────────────────────────────────────
    cur.execute(
        """CALL ingest_data(
            %s, %s, %s, %s, %s,
            %s::age_type, %s, %s, %s, %s,
            %s, %s::objective_type, %s, %s::protocol_type,
            %s::slicing_direction_type, %s, %s, %s,
            %s, %s::shrinkage_type, %s::age_scale_type,
            %s::gender_type, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )""",
        (
            neuron_name,        # a_neuron_name
            archive_name,       # archive_name
            archive_url,        # archive_url
            species,            # a_species
            expcond,            # a_expcond
            age,                # a_age
            region_id,          # a_region_id
            celltype_id,        # a_celltype_id
            dep_date,           # a_depositiondate
            upl_date,           # a_uploaddate
            magnification,      # magnification
            objective,          # objective
            orig_format,        # a_originalformat
            protocol,           # protocol
            slicing_dir,        # a_slicing_direction
            thickness,          # slicingthickness
            stain,              # a_staining
            strain,             # a_strain
            None,               # a_has_soma (not available from MySQL view)
            shrinkage,          # shrinkage
            age_scale,          # age_scale
            gender,             # gender
            max_age,            # max_age
            min_age,            # min_age
            min_weight,         # min_weight
            max_weight,         # max_weight
            note,               # note
            pmid,               # a_pmid
            doi,                # a_doi
            None,               # a_summary_meas_id (no measurements yet)
            shrinkage_value_id, # a_shrinkagevalue_id
            reconstruction,     # a_reconstruction_software
            url_reference,      # a_url_reference
            0,                  # a_neuron_id (INOUT, placeholder)
        ),
    )

    # ── 8. Get neuron_id and set oldid ───────────────────────────────────
    cur.execute("SELECT id FROM neuron WHERE name = %s", (neuron_name,))
    result = cur.fetchone()
    if not result:
        log.error("ERROR %s — neuron not found after ingest_data", neuron_name)
        return "error"
    neuron_id = result[0]

    cur.execute(
        "UPDATE neuron SET oldid = %s WHERE id = %s", (mysql_id, neuron_id)
    )

    # ── 9. Insert neuron_structure ───────────────────────────────────────
    morph_attr = safe_int(row.get("morph_attributes"))
    domain_map = {
        "ax_comp": "AX",
        "den_comp": "BS",
        "neu_comp": "NEU",
        "pr_comp": "PR",
    }
    for col, domain in domain_map.items():
        comp_val = row.get(col)
        if comp_val is not None:
            completeness = COMPLETENESS_MAP.get(str(comp_val))
            if completeness:
                cur.execute(
                    """INSERT INTO neuron_structure
                           (neuron_id, completeness, domain, morph_attributes)
                       VALUES (%s, %s::completeness_type,
                               %s::domain_type, %s)""",
                    (neuron_id, completeness, domain, morph_attr),
                )

    log.info("OK    %s (id=%d, oldid=%d)", neuron_name, neuron_id, mysql_id)
    return "imported"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Import neurons from MySQL export_neuron view into PostgreSQL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate mapping without inserting data",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max number of neurons to process (0 = all)",
    )
    parser.add_argument(
        "--neuron-id",
        type=int,
        default=0,
        help="Import only the neuron with this MySQL neuron_id",
    )
    args = parser.parse_args()

    # ── Connect to MySQL ──────────────────────────────────────────────────
    log.info(
        "Connecting to MySQL %s@%s/%s",
        cfg.mysql_user, cfg.mysql_host, cfg.mysql_db,
    )
    my_conn = mysql.connector.connect(
        host=cfg.mysql_host,
        user=cfg.mysql_user,
        password=cfg.mysql_password,
        database=cfg.mysql_db,
    )
    my_cur = my_conn.cursor(dictionary=True)

    # ── Relax sql_mode (the view uses non-aggregated GROUP BY columns) ───
    my_cur.execute("SET SESSION sql_mode = ''")

    # ── Recreate view without DEFINER if needed ───────────────────────────
    try:
        my_cur.execute("SELECT 1 FROM export_neuron LIMIT 1")
        my_cur.fetchall()
    except mysql.connector.errors.DatabaseError:
        log.info("Recreating export_neuron view without DEFINER …")
        view_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "mysqlview.sql"
        )
        with open(view_path) as f:
            view_sql = f.read()
        # Strip the DEFINER / ALGORITHM / SQL SECURITY prefix
        as_pos = view_sql.upper().find(" VIEW ")
        if as_pos >= 0:
            view_sql = "CREATE OR REPLACE" + view_sql[as_pos:]
        # Remove SQL SECURITY DEFINER if still present
        view_sql = view_sql.replace("SQL SECURITY DEFINER ", "")
        my_cur.execute(view_sql)
        my_conn.commit()
        log.info("View recreated successfully")

    # ── Build query ───────────────────────────────────────────────────────
    query = "SELECT * FROM export_neuron"
    params = []
    if args.neuron_id:
        query += " WHERE neuron_id = %s"
        params.append(args.neuron_id)
    if args.limit:
        query += " LIMIT %s"
        params.append(args.limit)

    log.info("Fetching neurons from MySQL …")
    my_cur.execute(query, params or None)
    rows = my_cur.fetchall()
    log.info("Fetched %d rows", len(rows))

    # ── Connect to PostgreSQL ─────────────────────────────────────────────
    log.info(
        "Connecting to PostgreSQL %s@%s/%s",
        cfg.dbuser, cfg.dbhost, cfg.dbsel,
    )
    pg_conn = psycopg2.connect(
        host=cfg.dbhost,
        database=cfg.dbsel,
        user=cfg.dbuser,
        password=cfg.dbpass,
    )
    pg_conn.autocommit = True  # required — stored procedures contain COMMIT

    # ── Import loop ───────────────────────────────────────────────────────
    counts = {"imported": 0, "skipped": 0, "error": 0}
    for i, row in enumerate(rows, 1):
        name = row.get("neuron_name", "?")
        try:
            result = import_neuron(pg_conn, row, dry_run=args.dry_run)
            counts[result] += 1
        except Exception:
            log.exception("ERROR %s", name)
            counts["error"] += 1

        if i % 500 == 0:
            log.info("Progress: %d / %d", i, len(rows))

    # ── Cleanup ───────────────────────────────────────────────────────────
    my_cur.close()
    my_conn.close()
    pg_conn.close()

    log.info(
        "Done. imported=%d  skipped=%d  errors=%d",
        counts["imported"], counts["skipped"], counts["error"],
    )


if __name__ == "__main__":
    main()
