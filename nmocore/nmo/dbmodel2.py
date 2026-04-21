# coding: utf-8
from sqlalchemy import ARRAY, Boolean, Column, Date, Enum, Float, ForeignKey, Integer, JSON, SmallInteger, String, Table, Text, UniqueConstraint, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


t_a_publication_id = Table(
    'a_publication_id', metadata,
    Column('id', Integer)
)


class Acknowledgement(Base):
    __tablename__ = 'acknowledgement'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    address1 = Column(String(512))
    address2 = Column(String(512))


class Archive(Base):
    __tablename__ = 'archive'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024))


class Celltype(Base):
    __tablename__ = 'celltype'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    path = Column(NullType)


class Duplicateaction(Base):
    __tablename__ = 'duplicateactions'

    id = Column(Integer, primary_key=True)
    neuron_name = Column(String(255), nullable=False)
    action = Column(String(31), nullable=False)


class Expcond(Base):
    __tablename__ = 'expcond'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(1024), nullable=False)


class Measurement(Base):
    __tablename__ = 'measurements'

    id = Column(Integer, primary_key=True)
    soma_surface = Column(Float(53))
    n_stems = Column(Integer)
    n_bifs = Column(Integer)
    n_branch = Column(Integer)
    width = Column(Float(53))
    height = Column(Float(53))
    depth = Column(Float(53))
    diameter = Column(Float(53))
    length = Column(Float(53))
    surface = Column(Float(53))
    volume = Column(Float(53))
    eucdistance = Column(Float(53))
    pathdistance = Column(Float(53))
    branch_order = Column(Float(53))
    contraction = Column(Float(53))
    fragmentation = Column(Float(53))
    partition_asymmetry = Column(Float(53))
    pk_classic = Column(Float(53))
    bif_ampl_local = Column(Float(53))
    bif_ampl_remote = Column(Float(53))
    fractal_dim = Column(Float(53))


t_measurementsview = Table(
    'measurementsview', metadata,
    Column('id', Integer),
    Column('name', String(255)),
    Column('soma_surface', Float(53)),
    Column('n_stems', Integer),
    Column('n_bifs', Integer),
    Column('n_branch', Integer),
    Column('width', Float(53)),
    Column('height', Float(53)),
    Column('depth', Float(53)),
    Column('diameter', Float(53)),
    Column('length', Float(53)),
    Column('surface', Float(53)),
    Column('volume', Float(53)),
    Column('eucdistance', Float(53)),
    Column('pathdistance', Float(53)),
    Column('branch_order', Float(53)),
    Column('contraction', Float(53)),
    Column('fragmentation', Float(53)),
    Column('partition_asymmetry', Float(53)),
    Column('pk_classic', Float(53)),
    Column('bif_ampl_local', Float(53)),
    Column('bif_ampl_remote', Float(53)),
    Column('fractal_dim', Float(53))
)


t_neuronview = Table(
    'neuronview', metadata,
    Column('id', Integer, index=True),
    Column('name', String(255), index=True),
    Column('age', Enum('adult', 'aged', 'embryonic', 'fetus', 'infant', 'larval', 'neonatal', 'not reported', 'old', 'tadpole', 'young', 'young adult', 'Not reported', name='age_type')),
    Column('region_array', JSON),
    Column('region_path', Text),
    Column('celltype_array', JSON),
    Column('celltype_path', Text),
    Column('archive_name', String(255)),
    Column('depositiondate', Date),
    Column('uploaddate', Date),
    Column('publication_journal', String(255)),
    Column('publication_title', String(255)),
    Column('publication_pmid', Integer),
    Column('expcond_name', String(1024)),
    Column('magnification', String(255)),
    Column('objective', Enum('dry', 'electron microscopy', 'glycerin', 'multiple', 'Not reported', 'oil', 'water', 'water or oil', 'IR-coated dipping intravital', name='objective_type')),
    Column('originalformat_name', String(255)),
    Column('slicing_direction', Enum('coronal', 'cross section', 'custom', 'flattened', 'horizontal', 'multiple', 'near-coronal', 'not applicable', 'Not reported', 'oblique coronal', 'oblique horizontal', 'parallel to the cortical surface', 'parasagittal', 'perpendicular to cortical layers', 'perpendicular to the long axis', 'sagittal', 'semi-coronal', 'semi-horizontal', 'tangential', 'thalamocortical', 'transverse', 'whole mount', 'Not applicable', 'Sagittal', name='slicing_direction_type')),
    Column('slicingthickness', String),
    Column('shrinkage', Enum('reported and corrected', 'reported and not corrected', 'Not reported', 'not applicable', 'Not applicable', name='shrinkage_type')),
    Column('shrinkagevalues', JSON),
    Column('age_scale', Enum('D', 'M', 'Y', 'Not reported', name='age_scale_type')),
    Column('gender', Enum('F', 'H', 'M', 'M/F', 'NR', 'Not reported', 'Not applicable', name='gender_type')),
    Column('max_age', Float(53)),
    Column('min_age', Float(53)),
    Column('min_weight', Float(53)),
    Column('max_weight', Float(53)),
    Column('note', Text),
    Column('url_reference', Text),
    Column('staining_name', String(255)),
    Column('protocol', Enum('culture', 'ex vivo', 'in ovo', 'in utero', 'in vitro', 'in vivo', 'Not reported', name='protocol_type')),
    Column('strain_name', String(255)),
    Column('species_name', String(255)),
    Column('structural_domain', JSON)
)


class Originalformat(Base):
    __tablename__ = 'originalformat'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    format_type = Column(Integer)


class Pubversion(Base):
    __tablename__ = 'pubversion'

    id = Column(Integer, primary_key=True)
    major = Column(Integer)
    minor = Column(Integer)
    patch = Column(Integer)
    active = Column(Boolean, server_default=text("true"))


t_pvecview = Table(
    'pvecview', metadata,
    Column('id', Integer),
    Column('name', String(255)),
    Column('distance', Float(53)),
    Column('coeffarray', JSON),
    Column('sfactor', Float(53))
)


class Region(Base):
    __tablename__ = 'region'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    path = Column(NullType, unique=True)


class Shrinkagevalue(Base):
    __tablename__ = 'shrinkagevalue'

    id = Column(Integer, primary_key=True)
    reported_value = Column(Float(53))
    reported_xy = Column(Float(53))
    reported_z = Column(Float(53))
    corrected_value = Column(Float(53))
    corrected_xy = Column(Float(53))
    corrected_z = Column(Float(53))


class Species(Base):
    __tablename__ = 'species'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))


class Staining(Base):
    __tablename__ = 'staining'

    id = Column(Integer, primary_key=True, unique=True)
    name = Column(String(255))


class Version(Base):
    __tablename__ = 'version'

    id = Column(Integer, primary_key=True)
    major = Column(Integer, nullable=False)
    minor = Column(Integer, nullable=False)
    patch = Column(Integer, nullable=False)
    active = Column(Boolean, server_default=text("true"))


class IngestedArchive(Base):
    __tablename__ = 'ingested_archives'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    date = Column(Date)
    message = Column(Text)
    status = Column(Enum('ready', 'read', 'error', 'ingested', 'partial', 'warning', 'public', name='status_type'))
    json = Column(JSON, server_default=text("'[]'::json"))
    version_id = Column(ForeignKey('version.id'))
    pubversion_id = Column(ForeignKey('pubversion.id'))
    foldername = Column(String(255))
    neurontotweet = Column(String(255))

    pubversion = relationship('Pubversion')
    version = relationship('Version')


class Publication(Base):
    __tablename__ = 'publication'

    id = Column(Integer, primary_key=True)
    pmid = Column(Integer, unique=True)
    doi = Column(String(255), unique=True)
    year = Column(SmallInteger)
    journal = Column(String(255))
    title = Column(String(255))
    first_author = Column(String(255))
    last_author = Column(String(255))
    species_id = Column(ForeignKey('species.id'))
    ocdate = Column(Date)
    specific_details = Column(String(255))
    related_page = Column(Integer)
    data_status = Column(String(255))
    literature_id = Column(String(128))
    abstract = Column(Text)
    url = Column(String(4096))

    species = relationship('Species')


class Strain(Base):
    __tablename__ = 'strain'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    species_id = Column(ForeignKey('species.id'))

    species = relationship('Species')


class Neuron(Base):
    __tablename__ = 'neuron'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    archive_id = Column(ForeignKey('archive.id', ondelete='CASCADE'), nullable=False)
    age = Column(Enum('adult', 'aged', 'embryonic', 'fetus', 'infant', 'larval', 'neonatal', 'not reported', 'old', 'tadpole', 'young', 'young adult', 'Not reported', name='age_type'))
    region_id = Column(ForeignKey('region.id'))
    celltype_id = Column(ForeignKey('celltype.id'), nullable=False)
    depositiondate = Column(Date, nullable=False)
    uploaddate = Column(Date, nullable=False)
    publication_id = Column(ForeignKey('publication.id'), nullable=False)
    expcond_id = Column(ForeignKey('expcond.id'))
    magnification = Column(String(255))
    summary_meas_id = Column(ForeignKey('measurements.id'))
    objective = Column(Enum('dry', 'electron microscopy', 'glycerin', 'multiple', 'Not reported', 'oil', 'water', 'water or oil', 'IR-coated dipping intravital', name='objective_type'))
    originalformat_id = Column(ForeignKey('originalformat.id'))
    slicing_direction = Column(Enum('coronal', 'cross section', 'custom', 'flattened', 'horizontal', 'multiple', 'near-coronal', 'not applicable', 'Not reported', 'oblique coronal', 'oblique horizontal', 'parallel to the cortical surface', 'parasagittal', 'perpendicular to cortical layers', 'perpendicular to the long axis', 'sagittal', 'semi-coronal', 'semi-horizontal', 'tangential', 'thalamocortical', 'transverse', 'whole mount', 'Not applicable', 'Sagittal', name='slicing_direction_type'))
    slicingthickness = Column(String)
    has_soma = Column(Boolean)
    shrinkage = Column(Enum('reported and corrected', 'reported and not corrected', 'Not reported', 'not applicable', 'Not applicable', name='shrinkage_type'))
    shrinkagevalue_id = Column(ForeignKey('shrinkagevalue.id'))
    age_scale = Column(Enum('D', 'M', 'Y', 'Not reported', name='age_scale_type'))
    gender = Column(Enum('F', 'H', 'M', 'M/F', 'NR', 'Not reported', 'Not applicable', name='gender_type'))
    max_age = Column(Float(53))
    min_age = Column(Float(53))
    min_weight = Column(Float(53))
    max_weight = Column(Float(53))
    note = Column(Text)
    url_reference = Column(Text)
    staining_id = Column(ForeignKey('staining.id'))
    protocol = Column(Enum('culture', 'ex vivo', 'in ovo', 'in utero', 'in vitro', 'in vivo', 'Not reported', name='protocol_type'))
    oldid = Column(Integer, unique=True)
    strain_id = Column(ForeignKey('strain.id'))
    reconstruction = Column(String)

    archive = relationship('Archive')
    celltype = relationship('Celltype')
    expcond = relationship('Expcond')
    originalformat = relationship('Originalformat')
    publication = relationship('Publication')
    region = relationship('Region')
    shrinkagevalue = relationship('Shrinkagevalue')
    staining = relationship('Staining')
    strain = relationship('Strain')
    summary_meas = relationship('Measurement')


t_export = Table(
    'export', metadata,
    Column('id', Integer, nullable=False),
    Column('neuron_id', ForeignKey('neuron.id')),
    Column('old_neuronid', Integer),
    Column('exportdate', Date),
    Column('status', Enum('ready', 'success', 'warning', 'error', name='exportstatus')),
    Column('message', Text)
)


class Ingestion(Base):
    __tablename__ = 'ingestion'
    __table_args__ = (
        UniqueConstraint('neuron_id', 'ingestion_date'),
    )

    id = Column(Integer, primary_key=True)
    neuron_id = Column(ForeignKey('neuron.id', ondelete='CASCADE'))
    ingestion_date = Column(Date)
    message = Column(Text)
    neuron_name = Column(String(255))
    archive = Column(String(255))
    status = Column(Enum('ready', 'read', 'error', 'ingested', 'partial', 'warning', 'public', name='status_type'))
    version_id = Column(ForeignKey('version.id'))

    neuron = relationship('Neuron')
    version = relationship('Version')


class NeuronSegment(Base):
    __tablename__ = 'neuron_segment'

    id = Column(Integer, primary_key=True)
    radius = Column(Integer, nullable=False)
    x = Column(Float(53), nullable=False)
    y = Column(Float(53), nullable=False)
    z = Column(Float(53), nullable=False)
    type = Column(Integer, nullable=False)
    path = Column(NullType)
    neuron_id = Column(ForeignKey('neuron.id'))

    neuron = relationship('Neuron')


class NeuronStructure(Base):
    __tablename__ = 'neuron_structure'

    id = Column(Integer, primary_key=True)
    neuron_id = Column(ForeignKey('neuron.id', ondelete='CASCADE'), nullable=False)
    measurements_id = Column(ForeignKey('measurements.id'))
    completeness = Column(Enum('Incomplete', 'Moderate', 'Complete', name='completeness_type'), nullable=False)
    domain = Column(Enum('AP', 'BS', 'AX', 'NEU', 'PR', name='domain_type'), nullable=False)
    morph_attributes = Column(SmallInteger)

    measurements = relationship('Measurement')
    neuron = relationship('Neuron')


class Pvec(Base):
    __tablename__ = 'pvec'

    id = Column(Integer, primary_key=True)
    neuron_id = Column(ForeignKey('neuron.id', ondelete='CASCADE'))
    distance = Column(Float(53))
    coeffs = Column(ARRAY(Float(precision=53)))
    sfactor = Column(Float(53))

    neuron = relationship('Neuron')
