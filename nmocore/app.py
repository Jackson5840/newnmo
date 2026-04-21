from redis.commands.search.field import TextField, NumericField
from redis.commands.search.indexDefinition import IndexDefinition

from ast import For, operator
import json
from urllib import request
from fastapi import FastAPI,Depends,status,Request,Query
from fastapi.responses import FileResponse,Response

from typing import Any, Iterator, List
from fastapi.responses import JSONResponse
from pydantic import errors
from pydantic.main import BaseModel
import sqlalchemy
from nmo import cfg, com,dbmodel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.expression import func
from sqlalchemy.sql import select
from sqlalchemy.ext.declarative import declarative_base
import time,random,io,zipfile,os,string,requests,shutil
from datetime import datetime

from fastapi_pagination import add_pagination
from fastapi_pagination import paginate as nosqlpag
from fastapi_pagination.ext.sqlalchemy import paginate
from typing import TypeVar, Generic
from fastapi_pagination.default import Params as BaseParams

from fastapi_pagination.links import Page as BasePage
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

import redis, pickle,walrus

app = FastAPI(root_path=os.environ.get("ROOT_PATH", ""))

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3002",
    "http://cng-nmo-main.orc.gmu.edu"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

r = redis.Redis(host=cfg.redishost, port=6379,db=0)

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'

engine = create_engine("postgresql://{}:{}@{}/{}".format(cfg.dbuser,cfg.dbpass,cfg.dbhost,cfg.dbsel))
SessionLocal = sessionmaker(autocommit=True, autoflush=True, bind=engine)

Base = declarative_base(bind=engine)

def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

T = TypeVar("T")

def zipfolder(adir):
    filelist = []
    s = io.BytesIO()
    zf = zipfile.ZipFile(s, "w")
    rootlen = len(adir) + 1
    for dirpath, dirnames, filenames in os.walk(adir,topdown=True):
        for file in filenames:
            fn = os.path.join(dirpath, file)
            zf.write(fn, fn[rootlen:])
    now = datetime.now()
    
    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    zip_filename = "archive{}.zip".format(dt_string)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = Response(s.getvalue(), media_type="application/x-zip-compressed", headers={
        'Content-Disposition': f'attachment;filename={zip_filename}'
    })

    return resp

class Params(BaseParams):
    size: int = Query(100, ge=1, le=500, description="Page size")

class NMOApiPage(BasePage[T], Generic[T]):
    """Default """
    status='success'
    idlistkey = ""
    __params_type__ = Params
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        fields = {"items": {"alias": "data"}}
        #fields = {"items": {"alias": "data"}}

class NMOApiRawPage(BasePage[T], Generic[T]):
    """Default """
    status='success'
    __params_type__ = Params
    class Config:
        #orm_mode = True
        #allow_population_by_field_name = False
        fields = {"items": {"alias": "data"}}
        #fields = {"items": {"alias": "data"}}

class NMOApiList(Generic[T]):
    """Default """
    status='success'
    class Config:
        fields = {"items": {"alias": "data"}}

class NMOCount(BaseModel):
    count: int

@app.get("/",response_model=NMOApiPage[dbmodel.Neuron])
async def get_users(db: Session = Depends(get_db)) -> Any:
    
    return paginate(db.query(dbmodel.t_neuronview))

@app.get("/quickstats/")
#@cache(namespace="nmoui", expire=86400)
async def quickstats(db: Session = Depends(get_db)) -> Any:
    hlkey = 'quickstats'
    aresp = r.get(hlkey)
    if aresp is not None:
        return JSONResponse(json.loads(aresp))
    mdl = dbmodel.t_browseview
    res = {}
    res['nspecies'] = db.query(mdl.c['species_name']).group_by(mdl.c['species_name']).count()
    res['nregions'] = db.query(mdl.c['region_name']).group_by(mdl.c['region_name']).count()
    res['ncelltypes'] = db.query(mdl.c['celltype_name']).group_by(mdl.c['celltype_name']).count()
    res['narchives'] = db.query(mdl.c['archive_name']).group_by(mdl.c['archive_name']).count()
    res['nneurons'] = db.query(mdl.c['neuron_name']).group_by(mdl.c['neuron_name']).count()
    aresp= jsonable_encoder(res)
    r.set(hlkey,json.dumps(aresp),ex=86400)
    return  JSONResponse(aresp)

@app.get("/clear")
async def clearcache():
    keys = r.keys('*')
    if len(keys) > 0:
        r.delete(*keys)
    return JSONResponse(jsonable_encoder({
        "status": "success"
    }))

@app.get("/feedsearch")
async def feedsearch():
    res = com.getdataforsearch()
    # Options for index creation
    index_def = IndexDefinition(
                    prefix = ["nmo_kw:"],
                    score = 0.5,
                    score_field = "doc_score",
    )

    # Schema definition
    schema = ( TextField("title"),
            TextField("body"),
    )

    # Create an index and pass in the schema
    #r.ft("nmo_idx").info
    try:
        r.ft("nmo_idx").dropindex(True)
    except redis.exceptions.ResponseError:
        pass
    r.ft("nmo_idx").create_index(schema, definition = index_def)

    for item in res:
        adoc = {
            "title": item[0],
            "body": item[1]
        }
        r.hset("nmo_kw:{}".format(item[0]), mapping = adoc)
    return JSONResponse(jsonable_encoder({
        "status": "success"
    }))

@app.get("/browse/{field}/{val}")
#@cache(namespace="nmoui", expire=86400)
async def browse(field: str, val: str, request:Request,idlistkey: str= Query(None), db: Session = Depends(get_db)) -> Any:
    hlkey = hash(frozenset(request.path_params.items() | {idlistkey}))
    aresp = r.get(hlkey)
    fieldmap = {
        'region': 'region_name',
        'celltype': 'celltype_name',
        'archive': 'archive_name',
        'species': 'species_name'
    }
    if field in fieldmap.keys():
        field = fieldmap[field]
    if aresp is not None:
        return JSONResponse(json.loads(aresp))
    if idlistkey is not None:
        idlist = pickle.loads(r.get(str(idlistkey)))
        if len(idlist) > 10000:
            idlist=idlist[:10000] # truncate if larger than 10k
    order =['archive_name','species_name','region_name','celltype_name']
    order.remove(field)
    mdl = dbmodel.t_browseview
    q = db.query(mdl.c[order[0]],mdl.c[order[1]],mdl.c[order[2]],mdl.c['neuron_name'],mdl.c['png_url'])
    if idlistkey is not None:
        q = q.filter(mdl.c['neuron_id'].in_(idlist))
    res = q.filter(mdl.c[field]==val).order_by(mdl.c[order[0]],mdl.c[order[1]],mdl.c[order[2]]).distinct().all()
    rootnode = {
        "text": val,
        "children": []
    }
    
    for item in res:
        depth=0    
        if len(rootnode['children']) == 0 or item[depth] != rootnode['children'][-1]['text']:
            rootnode['children'].append({
                "text": item[depth],
                "children": []
            })
        depth=1
        if len(rootnode['children'][-1]['children']) == 0 or item[depth] != rootnode['children'][-1]['children'][-1]['text']:
            rootnode['children'][-1]['children'].append({
                "text": item[depth],
                "children": []
            })
        depth=2
        if len(rootnode['children'][-1]['children'][-1]['children']) == 0 or item[depth] != rootnode['children'][-1]['children'][-1]['children'][-1]['text']:
            rootnode['children'][-1]['children'][-1]['children'].append({
                "text": item[depth],
                "children": []
            })
        depth=3
        rootnode['children'][-1]['children'][-1]['children'][-1]['children'].append({
            "text": item[depth],
            "a_attr": {
                "imgurl": item[4],
                "href": "neuroninfo.html?name={}".format(item[depth])
            }
        })
    aresp= jsonable_encoder({
        'data': [rootnode],
        'size': len(res)
    })
    r.set(hlkey,json.dumps(aresp),ex=86400)
    return  JSONResponse(aresp)

@app.get("/search/{keyword}",response_model=NMOApiPage[dbmodel.Neuron])
async def keywordsearch(keyword: str,request: Request, db: Session = Depends(get_db)) -> Any:

    hlkey = hash("kwsearch" + keyword)
    aresp = r.get(hlkey)
    if aresp is not None:
        return pickle.loads(aresp)
    res = r.ft("nmo_idx").search(redis.commands.search.query.Query(keyword).paging(0, 100000))

    ids =[int(item.title) for item in res.docs]
    idlistkey = str(hash(tuple(ids)))
    r.set(idlistkey,pickle.dumps(ids),ex=500000)
    mdl = dbmodel.t_neuronview
    q = db.query(mdl).filter(mdl.c['id'].in_(ids))
    aresp= paginate(q)
    aresp.idlistkey = idlistkey
    r.set(hlkey,pickle.dumps(aresp),ex=500000)
    return aresp

@app.get("/neuron/",response_model=NMOApiPage[dbmodel.Neuron])
async def getneuron(request: Request, db: Session = Depends(get_db)) -> Any:
    
    kv = request.query_params.multi_items()    
    hlkey = hash(frozenset(kv))
    aresp = r.get(hlkey)
    if aresp is not None:
        return pickle.loads(aresp)

    #dictparams = dict(request.query_params)
    d = {}
    [d[t[0]].append(t[1]) if t[0] in list(d.keys()) 
 else d.update({t[0]: [t[1]]}) for t in kv if t[1]]
    if 'page' in d.keys():
        d.pop('page')
    if 'size' in d.keys():
        d.pop('size')
    if 'browse' in d.keys():
        d.pop('browse')

        
    
    mdl = dbmodel.t_neuronview

    if 'idlistkey' in d.keys():
        idlistkey= d.pop('idlistkey')[0]
        idlist = pickle.loads(r.get(str(idlistkey)))
        return paginate(db.query(mdl).filter(mdl.c['id'].in_(idlist)))

    if 'random' in d.keys():
        return nosqlpag(db.query(mdl).order_by(func.random()).limit(int(d['random'][0])).all())
    
    #handle region and celltype and pop out fields from dict
    #use ltree query to get ids and then continue
    
    hasregions = False
    path = ""
    if ('region3' in d.keys()):
        path= d.pop('region3')[0]
        d.pop('region2')[0]
        d.pop('region1')[0]
    elif ('region2' in d.keys()):
        path= d.pop('region2')[0]
        d.pop('region1')[0]
    elif ('region1' in d.keys()):
        path= d.pop('region1')[0]
    if path:
        
        rnids =db.execute("""
        SELECT neuron.id from neuron JOIN region 
        ON neuron.region_id = region.id 
        wHERE '{}' @> region.path""".format(path)).fetchall()
        hasregions=True
        rnids = [item[0] for item in rnids]
    
    hascelltypes = False
    path = ""
    if ('celltype3' in d.keys()):
        path= d.pop('celltype3')[0]
        d.pop('celltype2')[0]
        d.pop('celltype1')[0]
    elif ('celltype2' in d.keys()):
        path= d.pop('celltype2')[0]
        d.pop('celltype1')[0]
    elif ('celltype1' in d.keys()):
        path= d.pop('celltype1')[0]
    if path:
        cnids =db.execute("""
        SELECT neuron.id from neuron JOIN celltype 
        ON neuron.celltype_id = celltype.id 
        wHERE '{}' @> celltype.path""".format(path)).fetchall()
        hascelltypes=True
        cnids = [item[0] for item in cnids]

    hasmorphattr = False
    if ('morph_attributes' in d.keys()):
        moa= d.pop('morph_attributes')[0]
        mnids = [item[0] for item in 
            db.execute("""
        SELECT neuron_id, MAX(morph_attributes) from neuron_structure 
        group by neuron_id
        HAVING MAX(morph_attributes) ={}""".format(moa)).fetchall()]
        hasmorphattr = True
    
    hasphysint = False
    if ('physint' in d.keys()):
        physint = d.pop('physint')
        physintjointmap = [
            ('Complete','Complete'),
            ('Moderate','Moderate'),
            ('Incomplete','Incomplete')

            
        ]
        for item in physint:
            
            stmt = """
            SELECT distinct neuron_id, MAX(id) as ma from neuron_structure 
            where domain = {} AND completeness = '{}'
        group by neuron_id"""
    if ('domain' in d.keys()):
        domain= d.pop('domain')[0]
        cness = d.pop('completeness')[0]
        if domain in ['Dendrites', 'Neurites','Axon','Processes']:
            stmt = """
        SELECT distinct neuron_id, MAX(id) as ma from neuron_structure 
        where 
        case 
            when domain = 'AX' THEN 'Axon'::TEXT
            when domain = 'PR' THEN 'Processes'::TEXT
            when domain = 'NEU' THEN 'Neurites'::TEXT
            when domain = 'BS' THEN 'Dendrites'::TEXT
            when domain = 'AP' THEN 'Dendrites'::TEXT
        END     
        = '{}' AND completeness = '{}'
        group by neuron_id""".format(domain,cness)
        else:
            stmt = "" #TODO expand for dendrites + axons
        pnids = [item[0] for item in db.execute(stmt).fetchall()]
        hasphysint = True
    
    
    hasstructdom = False
    if ('struct_domain' in d.keys()):
        stdo= int(d.pop('struct_domain')[0])
        stdomap = ['{"AX","DEN"}','{"DEN"}','{"AX","DEN"}','{"DEN"}','{"AX"}','{"AX"}','{"NEU"}','{"NEU"}','{"PR"}','{"PR"}']
        stsommap = [0,0,1,1,0,1,0,1,0,1]
        sres = db.execute("""
        SELECT distinct neuron.id,domagg
                from neuron
        INNER JOIN
                (
        SELECT neuron_id as nid,
        array_agg(
            DISTINCT (CASE 
                WHEN neuron_structure.domain = 'AP' THEN 'DEN'::TEXT
                WHEN neuron_structure.domain = 'BS' THEN 'DEN'::TEXT
                WHEN neuron_structure.domain = 'AX' THEN 'AX'::TEXT
                WHEN neuron_structure.domain = 'NEU' THEN 'NEU'::TEXT
                WHEN neuron_structure.domain = 'PR' THEN 'PR'::TEXT
                
            END)) as domagg from neuron_structure group by nid) as agarr
        ON neuron.id = agarr.nid
        and  agarr.domagg = '{}'
        AND has_soma = {}::boolean""".format(stdomap[stdo],stsommap[stdo])).fetchall()
        snids = [item[0] for item in sres]
        hasstructdom = True
    
    opfields = ["max_age","min_age","max_weight","min_weight"]
    fieldstmt = []
    hasopfields = False
    for item in opfields:
        if item in d.keys():
            hasopfields = True
            fieldval= d.pop(item)
            opkey = "{}_op".format(item) 
            if opkey in d.keys():
                opval = d.pop(opkey)
            else:
                opval = "="
        

            fieldstmt.append('{} {} {}'.format(item,opval[0],fieldval[0]))
    # fieldopsquery
    if hasopfields:
        fres = db.execute("SELECT id FROM neuronview WHERE {}".format(' AND '.join(fieldstmt))).all()
        fids = [item[0] for item in fres]
    
    #multivalue part
    mv = {}
    qdict = {}
    for item in d:
        if len(d[item])>1:
            mv[item] = d[item]
        else:
            qdict[item] = d[item][0]
    
    # first query single value part
    q = db.query(mdl).filter_by(**qdict)
    # build query for multi value part
    for item in mv:
        q = q.filter(mdl.c[item].in_(mv[item]))
    
    # add regions anc cell types
    if hasregions:
        q=q.filter(mdl.c['id'].in_(rnids))
    if hascelltypes:
        q=q.filter(mdl.c['id'].in_(cnids))
    if hasmorphattr:
        q=q.filter(mdl.c['id'].in_(mnids))
    if hasphysint:
        q=q.filter(mdl.c['id'].in_(pnids))
    if hasstructdom:
        q=q.filter(mdl.c['id'].in_(snids))
    if hasopfields:
        q=q.filter(mdl.c['id'].in_(fids))
    ids =[item['id'] for item in q.all()]
    idlistkey = str(hash(tuple(ids)))
    r.set(idlistkey,pickle.dumps(ids),ex=86400)
    aresp= paginate(q)
    aresp.idlistkey = idlistkey
    r.set(hlkey,pickle.dumps(aresp),ex=86400)
    return aresp

@app.get("/measurements/",response_model=NMOApiPage[dbmodel.Measurements])
async def getmeasurements(request: Request,db: Session = Depends(get_db)) -> Any:
    dictparams = dict(request.query_params)
    kv = request.query_params.multi_items()
    d = {}
    [d[t[0]].append(t[1]) if t[0] in list(d.keys()) 
 else d.update({t[0]: [t[1]]}) for t in kv if t[1]]
    if 'page' in d.keys():
        d.pop('page')
    if 'size' in d.keys():
        d.pop('size')
    

    mdl = dbmodel.t_measurementsview

    # if name is provided, return only one entry that is potentially matching
    if 'name' in d.keys():
        return paginate(db.query(mdl).filter(mdl.c['name']==d.pop('name')[0]))
    mv = {}
    qdict = {}
    fieldops= {}
    for item in d:
        if item[-3:] == '_op':
            afield = item[:-3]
            anop = d[item][0]
            fieldops[afield] = anop
        elif len(d[item])>1:
            mv[item] = d[item]
        else:
            qdict[item] = d[item][0]
    
    fieldstmt = []
    for item in fieldops:
        anop = fieldops[item]
        val =  d[item][0]

        fieldstmt.append('{} {} {}'.format(item,anop,val))
    # fieldopsquery
    res = db.execute("SELECT * FROM measurementsview WHERE {}".format(' AND '.join(fieldstmt))).all()

    ids = [item[0] for item in res]

    idlistkey = str(hash(tuple(ids)))
    r.set(idlistkey,pickle.dumps(ids),ex=86400)
    aresp = nosqlpag(res)
    aresp.idlistkey = idlistkey
    return aresp
    

@app.get("/pvec/{name}",response_model=NMOApiPage[dbmodel.Pvec])
async def getpvec(name: str, db: Session = Depends(get_db)) -> Any:
    mdl = dbmodel.t_pvecview
    return paginate(db.query(mdl).filter_by(name=name))

@app.get("/neuron/n/",response_model=NMOCount)
async def getneuron(request: Request, db: Session = Depends(get_db)) -> Any:
    params = request.query_params
    mdl = dbmodel.t_neuronview
    q = {"count": db.query(mdl).filter_by(**params).count()}
    return JSONResponse(jsonable_encoder(q))

    

""" @app.get("/metavals/",response_model=NMOApiPage[dbmodel.Metadatavals])
@cache(namespace="nmoui", expire=86400)
async def metavals(fields: List[str] = Query(None), db: Session = Depends(get_db)) -> Any:
    mdl = dbmodel.t_neuronview
    return JSONResponse(jsonable_encoder([
        {
            'field': afield, 
            'vals': [item[0] for item in db.query(mdl.c[afield]).order_by(mdl.c[afield]).distinct().all()]
        } for afield in fields
    ]))
 """

@app.get("/metavals/",response_model=NMOApiPage[dbmodel.Metadatavals])
async def metavals(fields: List[str] = Query(None),parent: str = Query(None),idlistkey: str = Query(None), db: Session = Depends(get_db)) -> Any:
    
    hlkey = hash(tuple(fields+[parent,idlistkey]))
    aresp = r.get(hlkey)
    if aresp is not None:
        return JSONResponse(json.loads(aresp))
      
    #get idlist from redis
    if idlistkey is not None:
        idlist = pickle.loads(r.get(str(idlistkey)))
        idclause= " AND neuron_id IN ({})".format(",".join([str(item) for item in idlist]))
    else:
        idclause = ""
        idlist = None

    

    if 'celltype' in fields:
        mdl=dbmodel.t_browseview
        q = db.query(mdl.c['celltype_name'])
        if idlist is not None:
            q = q.filter(mdl.c['neuron_id'].in_(tuple(idlist)))
        res = q.order_by(mdl.c['celltype_name']).distinct().all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'celltype', 
                'vals': [item[0] for item in res]
            }
        ]))
    if 'region' in fields:
        mdl=dbmodel.t_browseview
        q = db.query(mdl.c['region_name'])
        if idlist is not None:
            q = q.filter(mdl.c['neuron_id'].in_(tuple(idlist)))
        res = q.order_by(mdl.c['region_name']).distinct().all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'region', 
                'vals': [item[0] for item in res]
            }
        ]))
    
    if 'region1' in fields:
        res = db.execute("SELECT name,path from region where nlevel(path)=1{}".format(idclause)).all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'region1', 
                'vals': res
            }
        ]))
    elif 'region2' in fields:
        res = db.execute("SELECT name,path from region where nlevel(path)=2 and path <@ '{}{}'".format(parent,idclause)).all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'region2', 
                'vals': res
            }
        ]))
    elif 'region3' in fields:
        res = db.execute("SELECT name,path from region where nlevel(path)>=3 and path <@ '{}{}'".format(parent,idclause)).all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'region3', 
                'vals': res
            }
        ]))
    if 'celltype1' in fields:
        res = db.execute("SELECT name,path from celltype where nlevel(path)=1{}".format(idclause)).all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'celltype1', 
                'vals': res
            }
        ]))
    elif 'celltype2' in fields:
        res = db.execute("SELECT name,path from celltype where nlevel(path)=2 and path <@ '{}{}'".format(parent,idclause)).all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'celltype2', 
                'vals': res
            }
        ]))
    elif 'celltype3' in fields:
        res = db.execute("SELECT name,path from celltype where nlevel(path)>=3 and path <@ '{}{}'".format(parent,idclause)).all()
        return JSONResponse(jsonable_encoder([
            {
                'field': 'celltype3', 
                'vals': res
            }
        ]))
    

    mdl = dbmodel.t_neuronview
    
    toencode = []
    for afield in fields:
        q= db.query(mdl.c[afield])
        if idlist is not None:
            q = q.filter(mdl.c.id.in_(tuple(idlist)))
        toencode.append({
            'field': afield, 
            'vals': [item[0] for item in q.order_by(mdl.c[afield]).distinct().all()]
        })

    aresp = jsonable_encoder(toencode)
    r.set(hlkey, json.dumps(aresp),ex=86400)
    return JSONResponse(aresp)

    

@app.get("/chartcount/{afield}/{cutoff}")
#@cache(namespace="nmoui", expire=86400)
async def chartcount(afield: str, cutoff:int, request: Request, db: Session = Depends(get_db)) -> Any:
    hlkey = hash(frozenset(request.path_params.items()))
    aresp = r.get(hlkey)
    if aresp is not None:
        return JSONResponse(json.loads(aresp))

    mdl = dbmodel.t_browseview
    dbres = db.query(mdl.c[afield],func.count(mdl.c['neuron_name'])).group_by(mdl.c[afield]).order_by(func.count(mdl.c['neuron_name']).desc()).all()
    res = [[item[0],item[1]]
    for item in dbres if item[1]>=cutoff]
    rem = ['Others',sum([item[1] for item in dbres if item[1]<cutoff])]
    res.append(rem)
    aresp= jsonable_encoder(res)
    r.set(hlkey,json.dumps(aresp),ex=86400)
    return JSONResponse(aresp)

@app.get("/metacount/{afield}",response_model=NMOApiPage[dbmodel.Fieldcountvals])
async def getneuronrnd(afield: str,detail:bool = True, db: Session = Depends(get_db)) -> Any:
    mdl = dbmodel.t_neuronview
    if detail:
        fieldcounts = [{
                'fieldvalue': item[0], 
                'count': db.query(mdl).filter_by(**{afield: item[0]}).count()
            } for item in db.query(mdl.c[afield]).distinct().all()]
    else:
        fieldcounts = []
    return nosqlpag([
        {
            'field': afield,
            'totalcount': db.query(mdl.c[afield]).distinct().count(),
            'fieldcounts': fieldcounts
        }
    ])

@app.get("/getzipped/")
def getzipped(names: List[str] = Query(None),aux: bool=0, db: Session = Depends(get_db)) -> Any:
    mdl = dbmodel.t_neuronview
    names_archives = db.query(mdl.c.name, mdl.c.archive_name,mdl.c.originalformat_name).filter(mdl.c.name.in_(tuple(names))).all()
    N=10
    foldername = ''.join(random.choices(string.ascii_letters + string.digits, k=N))
    if not os.path.exists(foldername):
        os.mkdir(foldername)
    for item in names_archives:
        archive = item[1].lower()
        neuronname = item[0]
        ending = item[2]
        fileurl = 'https://neuromorpho.org/dableFiles/{}/CNG%20version/{}.CNG.swc'.format(archive,neuronname)
        r = requests.get(fileurl,verify=False)
        archivepath = os.path.join(foldername,item[1])
        if not os.path.exists(archivepath):
            os.mkdir(archivepath)
        swcpath = os.path.join(archivepath,'CNG version')
        if not os.path.exists(swcpath):
            os.mkdir(swcpath)
        fp = os.path.join(swcpath,'{}.CNG.swc'.format(neuronname))
        with open(fp,'wb') as f:
            f.write(r.content)
        if aux:
            srcurl = 'https://neuromorpho.org/dableFiles/{}/Source-Version/{}.{}'.format(archive,neuronname,ending)
            stdurl = 'https://neuromorpho.org/dableFiles/{}/Remaining%20issues/{}.CNG.swc.std'.format(archive,neuronname)
            stdorgurl = 'https://neuromorpho.org/dableFiles/{}/Standardization%20log/{}.std'.format(archive,neuronname)
            r = requests.get(srcurl,verify=False)
            srcpath = os.path.join(archivepath,'Source-Version')
            if not os.path.exists(srcpath):
                os.mkdir(srcpath)
            fp = os.path.join(srcpath,'{}.{}'.format(neuronname,ending))
            with open(fp,'wb') as f:
                f.write(r.content)
            
            r = requests.get(stdurl,verify=False)
            stdpath = os.path.join(archivepath,'Remaining issues')
            if not os.path.exists(stdpath):
                os.mkdir(stdpath)
            fp = os.path.join(stdpath,'{}.CNG.swc.std'.format(neuronname))
            with open(fp,'wb') as f:
                f.write(r.content)
            
            r = requests.get(stdorgurl,verify=False)
            stdorgpath = os.path.join(archivepath,'Standardization log')
            if not os.path.exists(stdorgpath):
                os.mkdir(stdorgpath)
            fp = os.path.join(stdorgpath,'{}.std'.format(neuronname))
            with open(fp,'wb') as f:
                f.write(r.content)
            

            
    res = zipfolder(foldername)
    shutil.rmtree(foldername)

    return res

"""@app.get("/neuron/{neuronid}",response_model=dbmodel.Neurondata)
async def getneuron(neuronid: int, db: Session = Depends(get_db)) -> Any:
    mdl = dbmodel.t_neuronview
    return {
        'data': db.query(mdl).filter_by(id = neuronid).first(),
        'status': 'success' 
    }
"""

add_pagination(app)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "errors": exc.errors(),
            "status": 'error'
        }),
    )

