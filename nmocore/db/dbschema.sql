--
-- NMO Database Schema
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Extensions
--

CREATE EXTENSION IF NOT EXISTS ltree WITH SCHEMA public;

--
-- Custom types
--

CREATE TYPE public.age_scale_type AS ENUM (
    'D', 'M', 'Y', 'Not reported'
);

CREATE TYPE public.age_type AS ENUM (
    'adult', 'aged', 'embryonic', 'fetus', 'infant', 'larval',
    'neonatal', 'not reported', 'old', 'tadpole', 'young',
    'young adult', 'Not reported'
);

CREATE TYPE public.completeness_type AS ENUM (
    'Incomplete', 'Moderate', 'Complete'
);

CREATE TYPE public.domain_type AS ENUM (
    'AP', 'BS', 'AX', 'NEU', 'PR'
);

CREATE TYPE public.exportstatus AS ENUM (
    'ready', 'success', 'warning', 'error'
);

CREATE TYPE public.gender_type AS ENUM (
    'F', 'H', 'M', 'M/F', 'NR', 'Not reported', 'Not applicable'
);

CREATE TYPE public.objective_type AS ENUM (
    'dry', 'electron microscopy', 'glycerin', 'multiple',
    'Not reported', 'oil', 'water', 'water or oil',
    'IR-coated dipping intravital'
);

CREATE TYPE public.protocol_type AS ENUM (
    'culture', 'ex vivo', 'in ovo', 'in utero',
    'in vitro', 'in vivo', 'Not reported'
);

CREATE TYPE public.shrinkage_type AS ENUM (
    'reported and corrected', 'reported and not corrected',
    'Not reported', 'not applicable', 'Not applicable'
);

CREATE TYPE public.slicing_direction_type AS ENUM (
    'coronal', 'cross section', 'custom', 'flattened', 'horizontal',
    'multiple', 'near-coronal', 'not applicable', 'Not reported',
    'oblique coronal', 'oblique horizontal',
    'parallel to the cortical surface', 'parasagittal',
    'perpendicular to cortical layers', 'perpendicular to the long axis',
    'sagittal', 'semi-coronal', 'semi-horizontal', 'tangential',
    'thalamocortical', 'transverse', 'whole mount',
    'Not applicable', 'Sagittal'
);

CREATE TYPE public.status_type AS ENUM (
    'ready', 'read', 'error', 'ingested', 'partial', 'warning', 'public'
);

--
-- Stored procedures
--

CREATE PROCEDURE public.ingest_celltype(IN celltype_names text[], IN a_celltype_path character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
DECLARE
        celltypes character varying ARRAY;
        item character varying;
        nAncestors int;
        ndbancestors int;
        a_celltype_id int;
        arrSize int;
        counter int;
        ancPath character varying;
BEGIN
        celltypes = regexp_split_to_array(a_celltype_path, '\.');
        nAncestors = array_length(celltypes, 1);
        arrSize = array_length(celltype_names, 1);
        IF nAncestors != arrSize THEN
                RAISE EXCEPTION 'Size of array and items indicated by path not matching'
                        USING hint = 'Please check input variables';
        END IF;

        select count(*) into ndbancestors from celltype where text2ltree(a_celltype_path) <@ path;
        IF ndbancestors != nAncestors THEN
                ancPath = '';
                for counter in 1..nAncestors
                LOOP
                       IF counter = 1 THEN
                        ancPath = celltypes[counter];
                       ELSE
                        ancPath = ancPath || '.' || celltypes[counter];
                       END IF;
                       Select celltype.id into a_celltype_id from celltype where celltype.path ~ lquery(ancPath);
                       IF a_celltype_id isnull THEN
                               insert into celltype(name,path) values (REPLACE(celltype_names[counter],'''',''),text2ltree(ancPath));
                       END IF;
                END LOOP;
        END IF;

COMMIT;
END;
 END;
$$;

CREATE PROCEDURE public.ingest_data(IN a_neuron_name character varying, IN archive_name character varying, IN archive_url character varying, IN a_species character varying, IN a_expcond character varying, IN a_age public.age_type, IN a_region_id integer, IN a_celltype_id integer, IN a_depositiondate date, IN a_uploaddate date, IN magnification character varying, IN objective public.objective_type, IN a_originalformat character varying, IN protocol public.protocol_type, IN a_slicing_direction public.slicing_direction_type, IN slicingthickness character varying, IN a_staining character varying, IN a_strain character varying, IN a_has_soma boolean, IN shrinkage public.shrinkage_type, IN age_scale public.age_scale_type, IN gender public.gender_type, IN max_age double precision, IN min_age double precision, IN min_weight double precision, IN max_weight double precision, IN note text, IN a_pmid integer, IN a_doi character varying, IN a_summary_meas_id integer, IN a_shrinkagevalue_id integer, IN a_reconstruction_software character varying, IN a_url_reference character varying, INOUT a_neuron_id integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
   DECLARE
        a_archive_id int;
        a_expcond_id int;
        a_originalformat_id int;
        a_publication_id int;
        a_staining_id int;
        a_strain_id int;
        a_species_id int;
        minpmid int;
BEGIN
        IF a_region_id = 0 THEN
               a_region_id = NULL;
        END IF;

        Select archive.id into a_archive_id from archive where archive.name = archive_name;
        IF a_archive_id isnull THEN
                INSERT INTO archive (name, url) VALUES (archive_name, archive_url);
                Select archive.id into a_archive_id from archive where archive.name = archive_name;
        END IF;

        select species.id into a_species_id from species where species.name = a_species;
        IF a_species_id isnull THEN
                INSERT INTO species (name) VALUES (a_species);
                Select species.id into a_species_id from species where species.name = a_species;
        END IF;

        Select expcond.id into a_expcond_id from expcond where expcond.name = a_expcond;
        IF a_expcond_id isnull THEN
                INSERT INTO expcond (name) VALUES (a_expcond);
                Select expcond.id into a_expcond_id from expcond where expcond.name = a_expcond;
        END IF;

        Select originalformat.id into a_originalformat_id from originalformat where originalformat.name = a_originalformat;
        IF a_originalformat_id isnull THEN
                INSERT INTO originalformat (name) VALUES (a_originalformat);
                Select originalformat.id into a_originalformat_id from originalformat where originalformat.name = a_originalformat;
        END IF;

        Select staining.id into a_staining_id from staining where staining.name = a_staining;
        IF a_staining_id isnull THEN
                INSERT INTO staining (name) VALUES (a_staining);
                Select staining.id into a_staining_id from staining where staining.name = a_staining;
        END IF;

        Select strain.id into a_strain_id from strain where strain.name = a_strain AND strain.species_id = a_species_id;
        IF a_strain_id isnull THEN
                INSERT INTO strain (name,species_id) VALUES (a_strain,a_species_id);
                Select strain.id into a_strain_id from strain where strain.name = a_strain AND strain.species_id = a_species_id;
        END IF;

        IF a_pmid < 0 THEN
                Select MIN(pmid) into minpmid from publication;
                IF minpmid < 0 THEN
                       minpmid = minpmid - 1;
                ELSE
                       minpmid = -1;
                END IF;
                Select publication.id into a_publication_id from publication where publication.doi = a_doi;
                IF a_publication_id isnull THEN
                        INSERT INTO publication (doi,pmid) VALUES (a_doi,minpmid);
                        Select publication.id into a_publication_id from publication where publication.doi = a_doi;
                END IF;
        ELSE
                Select publication.id into a_publication_id from publication where publication.pmid = a_pmid;
                if a_doi = '' THEN
                       a_doi = NULL;
                END IF;
                IF a_publication_id isnull THEN
                        INSERT INTO publication (doi,pmid) VALUES (a_doi,a_pmid);
                        Select publication.id into a_publication_id from publication where publication.pmid = a_pmid;
                END IF;
        END IF;

        raise notice 'Value: %', a_publication_id;

        INSERT INTO neuron(name,archive_id, has_soma, age,region_id,celltype_id,depositiondate,uploaddate,publication_id,expcond_id,magnification,summary_meas_id,objective,originalformat_id,protocol,slicing_direction,slicingthickness,staining_id,shrinkage,shrinkagevalue_id,age_scale,gender,max_age,min_age,min_weight,max_weight,note,url_reference, strain_id, reconstruction)
        VALUES(a_neuron_name, a_archive_id, a_has_soma,
                a_age,a_region_id, a_celltype_id, a_depositiondate, a_uploaddate, a_publication_id, a_expcond_id, magnification, a_summary_meas_id, objective, a_originalformat_id, protocol, a_slicing_direction, slicingthickness, a_staining_id, shrinkage, a_shrinkagevalue_id, age_scale, gender, max_age,min_age,min_weight,max_weight,note, a_url_reference, a_strain_id, a_reconstruction_software);
        select neuron.id into a_neuron_id from neuron where neuron.name = a_neuron_name;
        UPDATE ingestion set status='read',ingestion_date = a_uploaddate, message='Read from source' WHERE ingestion.neuron_name = a_neuron_name;

COMMIT;
END;
 END;
$$;

CREATE PROCEDURE public.ingest_region(IN reg_names text[], IN a_region_path character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
DECLARE
        regions character varying ARRAY;
        item character varying;
        nAncestors int;
        ndbancestors int;
        a_region_id int;
        arrSize int;
        counter int;
        ancPath character varying;
BEGIN
        regions = regexp_split_to_array(a_region_path, '\.');
        nAncestors = array_length(regions, 1);
        arrSize = array_length(reg_names, 1);
        IF nAncestors != arrSize THEN
                RAISE EXCEPTION 'Size of array and items indicated by path not matching'
                        USING hint = 'Please check input variables';
        END IF;

        select count(*) into ndbancestors from region where text2ltree(a_region_path) <@ path;
        IF ndbancestors != nAncestors THEN
                ancPath = '';
                for counter in 1..nAncestors
                LOOP
                       IF counter = 1 THEN
                        ancPath = regions[counter];
                       ELSE
                        ancPath = ancPath || '.' || regions[counter];
                       END IF;
                       Select region.id into a_region_id from region where region.path ~ lquery(ancPath);
                       IF a_region_id isnull THEN
                               insert into region(name,path) values (REPLACE(reg_names[counter],'''',''),text2ltree(ancPath));
                       END IF;
                END LOOP;
        END IF;

COMMIT;
END;
 END;
$$;

--
-- Tables
--

SET default_tablespace = '';
SET default_table_access_method = heap;

CREATE TABLE public.acknowledgement (
    id integer NOT NULL,
    name character varying,
    address1 character varying(512),
    address2 character varying(512)
);

ALTER TABLE public.acknowledgement ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.acknowledgement_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.archive (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    url character varying(1024)
);

ALTER TABLE public.archive ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.archive_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.celltype (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    path public.ltree
);

ALTER TABLE public.celltype ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.celltype_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.duplicateactions (
    id integer NOT NULL,
    neuron_name character varying(255) NOT NULL,
    action character varying(31) NOT NULL
);

ALTER TABLE public.duplicateactions ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.duplicateactions_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.expcond (
    id integer NOT NULL,
    name character varying(1024) NOT NULL
);

ALTER TABLE public.expcond ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.expcond_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.export (
    id integer NOT NULL,
    neuron_id integer,
    old_neuronid integer,
    exportdate date,
    status public.exportstatus,
    message text
);

ALTER TABLE public.export ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.export_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.ingested_archives (
    id integer NOT NULL,
    name character varying(255),
    date date,
    message text,
    status public.status_type,
    "json" json DEFAULT '[]'::json,
    version_id integer,
    pubversion_id integer,
    foldername character varying(255),
    neurontotweet character varying(255)
);

ALTER TABLE public.ingested_archives ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ingested_archives_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.ingestion (
    id integer NOT NULL,
    neuron_id integer,
    ingestion_date date,
    message text,
    neuron_name character varying(255),
    archive character varying(255),
    status public.status_type,
    version_id integer
);

ALTER TABLE public.ingestion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ingestion_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.measurements (
    id integer NOT NULL,
    soma_surface double precision,
    n_stems integer,
    n_bifs integer,
    n_branch integer,
    width double precision,
    height double precision,
    depth double precision,
    diameter double precision,
    length double precision,
    surface double precision,
    volume double precision,
    eucdistance double precision,
    pathdistance double precision,
    branch_order double precision,
    contraction double precision,
    fragmentation double precision,
    partition_asymmetry double precision,
    pk_classic double precision,
    bif_ampl_local double precision,
    bif_ampl_remote double precision,
    fractal_dim double precision
);

ALTER TABLE public.measurements ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.measurements_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.neuron (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    archive_id integer NOT NULL,
    age public.age_type,
    region_id integer,
    celltype_id integer NOT NULL,
    depositiondate date NOT NULL,
    uploaddate date NOT NULL,
    publication_id integer NOT NULL,
    expcond_id integer,
    magnification character varying(255),
    summary_meas_id integer,
    objective public.objective_type,
    originalformat_id integer,
    slicing_direction public.slicing_direction_type,
    slicingthickness character varying,
    has_soma boolean,
    shrinkage public.shrinkage_type,
    shrinkagevalue_id integer,
    age_scale public.age_scale_type,
    gender public.gender_type,
    max_age double precision,
    min_age double precision,
    min_weight double precision,
    max_weight double precision,
    note text,
    url_reference text,
    staining_id integer,
    protocol public.protocol_type,
    oldid integer,
    strain_id integer,
    reconstruction character varying
);

ALTER TABLE public.neuron ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.neuron_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.neuron_segment (
    id integer NOT NULL,
    radius integer NOT NULL,
    x double precision NOT NULL,
    y double precision NOT NULL,
    z double precision NOT NULL,
    type integer NOT NULL,
    path public.ltree,
    neuron_id integer
);

ALTER TABLE public.neuron_segment ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.neuron_segment_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.neuron_structure (
    id integer NOT NULL,
    neuron_id integer NOT NULL,
    measurements_id integer,
    completeness public.completeness_type NOT NULL,
    domain public.domain_type NOT NULL,
    morph_attributes smallint
);

ALTER TABLE public.neuron_structure ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.neuron_structure_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.originalformat (
    id integer NOT NULL,
    name character varying(255),
    format_type integer
);

ALTER TABLE public.originalformat ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.originalformat_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.publication (
    id integer NOT NULL,
    pmid integer,
    doi character varying(255),
    year smallint,
    journal character varying(255),
    title character varying(255),
    first_author character varying(255),
    last_author character varying(255),
    species_id integer,
    ocdate date,
    specific_details character varying(255),
    related_page integer,
    data_status character varying(255),
    literature_id character varying(128),
    abstract text,
    url character varying(4096)
);

ALTER TABLE public.publication ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.publication_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.pubversion (
    id integer NOT NULL,
    major integer,
    minor integer,
    patch integer,
    active boolean DEFAULT true
);

ALTER TABLE public.pubversion ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.pubversion_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.pvec (
    id integer NOT NULL,
    neuron_id integer,
    distance double precision,
    coeffs double precision[],
    sfactor double precision
);

ALTER TABLE public.pvec ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.pvec_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.region (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    path public.ltree
);

ALTER TABLE public.region ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.region_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.shrinkagevalue (
    id integer NOT NULL,
    reported_value double precision,
    reported_xy double precision,
    reported_z double precision,
    corrected_value double precision,
    corrected_xy double precision,
    corrected_z double precision
);

ALTER TABLE public.shrinkagevalue ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.shrinkagevalue_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.species (
    id integer NOT NULL,
    name character varying(255)
);

ALTER TABLE public.species ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.species_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.staining (
    id integer NOT NULL,
    name character varying(255)
);

ALTER TABLE public.staining ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.staining_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.strain (
    id integer NOT NULL,
    name character varying(255),
    species_id integer
);

ALTER TABLE public.strain ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.strain_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

CREATE TABLE public.version (
    id integer NOT NULL,
    major integer NOT NULL,
    minor integer NOT NULL,
    patch integer NOT NULL,
    active boolean DEFAULT true
);

ALTER TABLE public.version ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.release_id_seq
    START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1
);

--
-- Materialized views
--

CREATE MATERIALIZED VIEW public.browseview AS
 SELECT neuron.id AS neuron_id,
    neuron.name AS neuron_name,
    region.name AS region_name,
    celltype.name AS celltype_name,
    archive.name AS archive_name,
    (('https://neuromorpho.org/images/imageFiles/' || (archive.name)::text || '/' || (neuron.name)::text) || '.png') AS png_url,
    species.name AS species_name
   FROM public.neuron
     JOIN public.archive ON (neuron.archive_id = archive.id)
     JOIN public.region ON (neuron.region_id = region.id)
     JOIN public.celltype ON (neuron.celltype_id = celltype.id)
     JOIN public.strain ON (neuron.strain_id = strain.id)
     JOIN public.species ON (strain.species_id = species.id)
  WITH NO DATA;

CREATE MATERIALIZED VIEW public.measurementsview AS
 SELECT neuron.id,
    neuron.name,
    measurements.soma_surface,
    measurements.n_stems,
    measurements.n_bifs,
    measurements.n_branch,
    measurements.width,
    measurements.height,
    measurements.depth,
    measurements.diameter,
    measurements.length,
    measurements.surface,
    measurements.volume,
    measurements.eucdistance,
    measurements.pathdistance,
    measurements.branch_order,
    measurements.contraction,
    measurements.fragmentation,
    measurements.partition_asymmetry,
    measurements.pk_classic,
    measurements.bif_ampl_local,
    measurements.bif_ampl_remote,
    measurements.fractal_dim
   FROM public.measurements
     JOIN public.neuron ON (neuron.summary_meas_id = measurements.id)
  WITH NO DATA;

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
    publication.title AS publication_title,
    publication.pmid AS publication_pmid,
    publication.doi AS publication_doi,
    expcond.name AS expcond_name,
    neuron.magnification,
    neuron.objective,
    originalformat.name AS originalformat_name,
    neuron.reconstruction,
    (('https://neuromorpho.org/images/imageFiles/' || (archive.name)::text || '/' || (neuron.name)::text) || '.png') AS png_url,
    neuron.slicing_direction,
    neuron.slicingthickness,
    neuron.shrinkage,
    ( SELECT row_to_json("row".*) AS row_to_json
           FROM ( SELECT shrinkagevalue_1.reported_value,
                    shrinkagevalue_1.reported_xy,
                    shrinkagevalue_1.reported_z,
                    shrinkagevalue_1.corrected_value,
                    shrinkagevalue_1.corrected_xy,
                    shrinkagevalue_1.corrected_z
                   FROM public.shrinkagevalue shrinkagevalue_1
                  WHERE shrinkagevalue_1.id = neuron.shrinkagevalue_id) "row") AS shrinkagevalues,
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
    strain.name AS strain_name,
    species.name AS species_name,
    ( SELECT json_agg(json_build_object('completeness', neuron_structure.completeness, 'domain', neuron_structure.domain, 'morph_attributes',
                CASE
                    WHEN neuron_structure.morph_attributes = 1 THEN 'Diameter, 2D, Angles'::text
                    WHEN neuron_structure.morph_attributes = 2 THEN 'Diameter, 3D, No Angles'::text
                    WHEN neuron_structure.morph_attributes = 3 THEN 'Diameter, 3D, Angles'::text
                    WHEN neuron_structure.morph_attributes = 4 THEN 'Diameter, 2D, No Angles'::text
                    WHEN neuron_structure.morph_attributes = 5 THEN 'No Diameter, 2D, Angles'::text
                    ELSE 'No Diameter, 3D, Angles'::text
                END)) AS a
           FROM public.neuron_structure
          WHERE neuron.id = neuron_structure.neuron_id
          GROUP BY neuron_structure.neuron_id) AS structural_domain
   FROM public.neuron
     JOIN public.archive ON (neuron.archive_id = archive.id)
     JOIN public.publication ON (neuron.publication_id = publication.id)
     JOIN public.expcond ON (neuron.expcond_id = expcond.id)
     JOIN public.region ON (neuron.region_id = region.id)
     JOIN public.celltype ON (neuron.celltype_id = celltype.id)
     JOIN public.originalformat ON (neuron.originalformat_id = originalformat.id)
     JOIN public.strain ON (neuron.strain_id = strain.id)
     JOIN public.species ON (strain.species_id = species.id)
     JOIN public.staining ON (neuron.staining_id = staining.id)
     JOIN public.shrinkagevalue ON (neuron.shrinkagevalue_id = shrinkagevalue.id)
  WITH NO DATA;

CREATE MATERIALIZED VIEW public.pvecview AS
 SELECT neuron.id,
    neuron.name,
    pvec.distance,
    array_to_json(pvec.coeffs) AS coeffarray,
    pvec.sfactor
   FROM public.pvec
     JOIN public.neuron ON (pvec.neuron_id = neuron.id)
  WITH NO DATA;

--
-- Primary keys
--

ALTER TABLE ONLY public.acknowledgement ADD CONSTRAINT acknowledgement_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.archive ADD CONSTRAINT archive_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.celltype ADD CONSTRAINT celltype_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.duplicateactions ADD CONSTRAINT duplicateactions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.expcond ADD CONSTRAINT experimentcondition_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.ingested_archives ADD CONSTRAINT ingested_archives_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.ingestion ADD CONSTRAINT ingestion_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.measurements ADD CONSTRAINT measurements_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT pk PRIMARY KEY (id);
ALTER TABLE ONLY public.neuron_segment ADD CONSTRAINT neuron_segment_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.neuron_structure ADD CONSTRAINT neuron_structure_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.originalformat ADD CONSTRAINT originalformat_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.publication ADD CONSTRAINT publication_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.pubversion ADD CONSTRAINT pubversion_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.pvec ADD CONSTRAINT pvec_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.region ADD CONSTRAINT region_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.version ADD CONSTRAINT release_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.shrinkagevalue ADD CONSTRAINT shrinkagevalue_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.species ADD CONSTRAINT species_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.staining ADD CONSTRAINT staining_pkey PRIMARY KEY (id);
ALTER TABLE ONLY public.strain ADD CONSTRAINT strain_pkey PRIMARY KEY (id);

--
-- Unique constraints
--

ALTER TABLE ONLY public.acknowledgement ADD CONSTRAINT acknowledgement_ix1 UNIQUE (name);
ALTER TABLE ONLY public.expcond ADD CONSTRAINT expcond_ix1 UNIQUE (id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_ix1 UNIQUE (name);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_ix2 UNIQUE (oldid);
ALTER TABLE ONLY public.ingestion ADD CONSTRAINT ingestion_neuron_id_ingestion_date_key UNIQUE (neuron_id, ingestion_date);
ALTER TABLE ONLY public.publication ADD CONSTRAINT publication_ix1 UNIQUE (pmid);
ALTER TABLE ONLY public.publication ADD CONSTRAINT publication_ix2 UNIQUE (doi);
ALTER TABLE ONLY public.region ADD CONSTRAINT region_ix1 UNIQUE (path);
ALTER TABLE ONLY public.staining ADD CONSTRAINT staining_ix1 UNIQUE (id);

--
-- Indexes
--

CREATE INDEX nvi1 ON public.neuronview USING btree (name);

--
-- Foreign keys
--

ALTER TABLE ONLY public.export ADD CONSTRAINT export_fk1 FOREIGN KEY (neuron_id) REFERENCES public.neuron(id);
ALTER TABLE ONLY public.ingested_archives ADD CONSTRAINT ingestedarchives_fk1 FOREIGN KEY (version_id) REFERENCES public.version(id);
ALTER TABLE ONLY public.ingested_archives ADD CONSTRAINT ingestedarchives_fk2 FOREIGN KEY (pubversion_id) REFERENCES public.pubversion(id);
ALTER TABLE ONLY public.ingestion ADD CONSTRAINT ingestion_fk1 FOREIGN KEY (neuron_id) REFERENCES public.neuron(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.ingestion ADD CONSTRAINT ingestion_fk2 FOREIGN KEY (version_id) REFERENCES public.version(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk1 FOREIGN KEY (archive_id) REFERENCES public.archive(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk2 FOREIGN KEY (region_id) REFERENCES public.region(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk3 FOREIGN KEY (celltype_id) REFERENCES public.celltype(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk4 FOREIGN KEY (publication_id) REFERENCES public.publication(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk5 FOREIGN KEY (expcond_id) REFERENCES public.expcond(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk7 FOREIGN KEY (summary_meas_id) REFERENCES public.measurements(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk8 FOREIGN KEY (originalformat_id) REFERENCES public.originalformat(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk9 FOREIGN KEY (shrinkagevalue_id) REFERENCES public.shrinkagevalue(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk10 FOREIGN KEY (staining_id) REFERENCES public.staining(id);
ALTER TABLE ONLY public.neuron ADD CONSTRAINT neuron_fk11 FOREIGN KEY (strain_id) REFERENCES public.strain(id);
ALTER TABLE ONLY public.neuron_segment ADD CONSTRAINT neuronsegment_fk1 FOREIGN KEY (neuron_id) REFERENCES public.neuron(id);
ALTER TABLE ONLY public.neuron_structure ADD CONSTRAINT neuronstructure_fk2 FOREIGN KEY (measurements_id) REFERENCES public.measurements(id);
ALTER TABLE ONLY public.neuron_structure ADD CONSTRAINT neuronstructure_fk3 FOREIGN KEY (neuron_id) REFERENCES public.neuron(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.publication ADD CONSTRAINT publication_fk1 FOREIGN KEY (species_id) REFERENCES public.species(id);
ALTER TABLE ONLY public.pvec ADD CONSTRAINT pvec_fk1 FOREIGN KEY (neuron_id) REFERENCES public.neuron(id) ON DELETE CASCADE;
ALTER TABLE ONLY public.strain ADD CONSTRAINT strain_fk1 FOREIGN KEY (species_id) REFERENCES public.species(id);

--
-- Refresh materialized views (empty but populated, avoids "has not been populated" errors)
--

REFRESH MATERIALIZED VIEW public.browseview;
REFRESH MATERIALIZED VIEW public.measurementsview;
REFRESH MATERIALIZED VIEW public.neuronview;
REFRESH MATERIALIZED VIEW public.pvecview;
