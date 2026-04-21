#!/bin/bash
# The bundled pglocdump.sql predates some schema changes the API expects:
#   - `browseview` materialized view does not exist in the dump
#   - `neuronview` in the dump is missing columns (e.g. publication_doi)
#
# We DROP + CREATE both views using the up-to-date definitions from
# nmocore/db/dbschema.sql, then REFRESH everything so the API can serve data
# immediately on first startup.
set -u

psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
-- --------------------------------------------------------------------------
-- neuronview (current schema, includes publication_doi)
-- --------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS public.neuronview CASCADE;

CREATE MATERIALIZED VIEW public.neuronview AS
 SELECT neuron.id,
    neuron.name,
    neuron.age,
    array_to_json(ARRAY( SELECT region_1.name
           FROM public.region region_1
          WHERE region_1.path OPERATOR(public.@>) ( SELECT region_2.path
                   FROM public.region region_2
                  WHERE region_2.id = neuron.region_id)
          ORDER BY region_1.path)) AS region_array,
    public.ltree2text(region.path) AS region_path,
    array_to_json(ARRAY( SELECT celltype_1.name
           FROM public.celltype celltype_1
          WHERE celltype_1.path OPERATOR(public.@>) ( SELECT celltype_2.path
                   FROM public.celltype celltype_2
                  WHERE celltype_2.id = neuron.celltype_id)
          ORDER BY celltype_1.path)) AS celltype_array,
    public.ltree2text(celltype.path) AS celltype_path,
    archive.name AS archive_name,
    neuron.depositiondate,
    neuron.uploaddate,
    publication.journal AS publication_journal,
    publication.title   AS publication_title,
    publication.pmid    AS publication_pmid,
    publication.doi     AS publication_doi,
    expcond.name        AS expcond_name,
    neuron.magnification,
    neuron.objective,
    originalformat.name AS originalformat_name,
    neuron.reconstruction,
    (('https://neuromorpho.org/images/imageFiles/' || (archive.name)::text || '/' || (neuron.name)::text) || '.png') AS png_url,
    neuron.slicing_direction,
    neuron.slicingthickness,
    neuron.shrinkage,
    ( SELECT row_to_json("row".*) AS row_to_json
        FROM ( SELECT sv.reported_value, sv.reported_xy, sv.reported_z,
                      sv.corrected_value, sv.corrected_xy, sv.corrected_z
                 FROM public.shrinkagevalue sv
                WHERE sv.id = neuron.shrinkagevalue_id) "row") AS shrinkagevalues,
    neuron.age_scale,
    neuron.gender,
    neuron.max_age,
    neuron.min_age,
    neuron.min_weight,
    neuron.max_weight,
    neuron.note,
    neuron.url_reference,
    staining.name AS staining_name,
    neuron.protocol,
    strain.name   AS strain_name,
    species.name  AS species_name,
    ( SELECT json_agg(json_build_object(
                'completeness', ns.completeness,
                'domain',       ns.domain,
                'morph_attributes',
                CASE
                    WHEN ns.morph_attributes = 1 THEN 'Diameter, 2D, Angles'::text
                    WHEN ns.morph_attributes = 2 THEN 'Diameter, 3D, No Angles'::text
                    WHEN ns.morph_attributes = 3 THEN 'Diameter, 3D, Angles'::text
                    WHEN ns.morph_attributes = 4 THEN 'Diameter, 2D, No Angles'::text
                    WHEN ns.morph_attributes = 5 THEN 'No Diameter, 2D, Angles'::text
                    ELSE 'No Diameter, 3D, Angles'::text
                END)) AS a
        FROM public.neuron_structure ns
       WHERE neuron.id = ns.neuron_id
       GROUP BY ns.neuron_id) AS structural_domain
   FROM public.neuron
     JOIN public.archive        ON neuron.archive_id        = archive.id
     JOIN public.publication    ON neuron.publication_id    = publication.id
     JOIN public.expcond        ON neuron.expcond_id        = expcond.id
     JOIN public.region         ON neuron.region_id         = region.id
     JOIN public.celltype       ON neuron.celltype_id       = celltype.id
     JOIN public.originalformat ON neuron.originalformat_id = originalformat.id
     JOIN public.strain         ON neuron.strain_id         = strain.id
     JOIN public.species        ON strain.species_id        = species.id
     JOIN public.staining       ON neuron.staining_id       = staining.id
     JOIN public.shrinkagevalue ON neuron.shrinkagevalue_id = shrinkagevalue.id
  WITH NO DATA;

CREATE INDEX IF NOT EXISTS neuronview_id_idx ON public.neuronview (id);

-- --------------------------------------------------------------------------
-- browseview (missing from older dumps)
-- --------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS public.browseview AS
    SELECT neuron.id   AS neuron_id,
           neuron.name AS neuron_name,
           region.name   AS region_name,
           celltype.name AS celltype_name,
           archive.name  AS archive_name,
           ('https://neuromorpho.org/images/imageFiles/' || archive.name::text || '/' || neuron.name::text) || '.png'
                         AS png_url,
           species.name  AS species_name
      FROM public.neuron
      JOIN public.archive  ON neuron.archive_id  = archive.id
      JOIN public.region   ON neuron.region_id   = region.id
      JOIN public.celltype ON neuron.celltype_id = celltype.id
      JOIN public.strain   ON neuron.strain_id   = strain.id
      JOIN public.species  ON strain.species_id  = species.id
    WITH NO DATA;

-- --------------------------------------------------------------------------
-- Populate everything
-- --------------------------------------------------------------------------
REFRESH MATERIALIZED VIEW public.neuronview;
REFRESH MATERIALIZED VIEW public.browseview;
REFRESH MATERIALIZED VIEW public.measurementsview;
REFRESH MATERIALIZED VIEW public.pvecview;
SQL
