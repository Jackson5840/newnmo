# coding: utf-8
from pydantic.main import BaseModel
from sqlalchemy import ARRAY, Boolean, Column, Date, Enum, Float, ForeignKey, Integer, JSON, SmallInteger, String, Table, Text, UniqueConstraint, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import LtreeType, Ltree
import datetime
from typing import Any, List, Union

Base = declarative_base()
metadata = Base.metadata


t_browseview = Table(
    'browseview', metadata,
    Column('neuron_id', Integer),
    Column('neuron_name', String(255)),
    Column('region_name', String(255), index=True),
    Column('celltype_name', String(255), index=True),
    Column('archive_name', String(255), index=True),
    Column('png_url', String(255)),
    Column('species_name', String(255),index=True))
 


t_neuronview = Table(
    'neuronview', metadata,
    Column('id', Integer, index=True),
    Column('name', String(255), index=True),
    Column('age', Enum('adult', 'aged', 'embryonic', 'fetus', 'infant', 'larval', 'neonatal', 'not reported', 'old', 'prepupa', 'tadpole', 'young', 'young adult', 'Not reported', name='age_type')),
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
    Column('publication_doi', String(255)),
    Column('expcond_name', String(1024)),
    Column('magnification', String(255)),
    Column('objective', Enum('dry', 'electron microscopy', 'glycerin', 'multiple', 'Not reported', 'oil', 'water', 'water or oil', 'IR-coated dipping intravital', name='objective_type')),
    Column('originalformat_name', String(255)),
    Column('reconstruction', String(255)),
    Column('png_url', String(255)),
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

t_pvecview = Table(
    'pvecview', metadata,
    Column('id', Integer),
    Column('name', String(255)),
    Column('distance', Float(53)),
    Column('coeffarray', JSON),
    Column('sfactor', Float(53))
)

Nested = Union[str,None]
NestNum = Union[float,None]
NestList = Union[list,None]


class Neuron(BaseModel):
    """
    Meta data model for a neuron 
    """
    id: int 
    name: str
    age: str
    region_array: list
    region_path: Union[str,None]
    celltype_array: list
    celltype_path: Union[str,None]
    archive_name: str
    depositiondate: datetime.date
    uploaddate: datetime.date
    publication_journal: Nested
    publication_title: Nested
    publication_pmid: int
    publication_doi: Union[str,None]
    expcond_name: str
    magnification: str
    objective: str
    originalformat_name: str
    reconstruction: str
    png_url: str
    slicing_direction: str
    slicingthickness: str
    shrinkage: str
    shrinkagevalues: Any
    age_scale: str
    gender: str
    max_age: NestNum
    min_age: NestNum
    min_weight: NestNum
    max_weight: NestNum
    note: Nested
    url_reference: Nested
    staining_name: str
    protocol: str
    strain_name: str
    species_name: str
    structural_domain: NestList
    class Config:
        orm_mode = True

class Measurements(BaseModel):
    """ 
    This is measurements from L-Measure
    """
    id: int
    name: str
    soma_surface: Union[float,None]
    n_stems: int
    n_bifs: int
    n_branch: int
    width: float
    height: float
    depth: float
    diameter: float
    length: float
    surface: float
    volume: float
    eucdistance: float
    pathdistance: float
    branch_order: float
    contraction: float
    fragmentation: float
    partition_asymmetry: float
    pk_classic: float
    bif_ampl_local: float
    bif_ampl_remote: float
    fractal_dim: float
    class Config:
        orm_mode = True

class Pvec(BaseModel):
    id: int
    name: str
    distance: float
    coeffarray: list
    sfactor: float
    class Config:
        orm_mode = True

class Neurondata(BaseModel):
    """
    Meta data model for a neuron request. Data contained in structure. 
    """
    data: Neuron
    status: str

class Metadatavals(BaseModel):
    """
    List of possible meta data values for an field of an entitity
    """
    field: str
    vals: List[str] = []
    class Config:
        orm_mode = True

class Fieldcount(BaseModel):
    fieldvalue: str
    count: int

class Fieldcountvals(BaseModel):
    """
    List of possible meta data values for an field of an entitity
    """
    field: str
    totalcount: int
    fieldcounts: List[Fieldcount] = []
    