import psycopg2
import psycopg2.extras
import paramiko
import mysql.connector as mysc
from . import cfg
from . import io
from datetime import datetime
import json


def pgconnect(f):
    #decorator for postgres operations
    def pgconnect_(*args, **kwargs):
        conn = psycopg2.connect(host=cfg.dbhost,database=cfg.dbsel, user=cfg.dbuser, password=cfg.dbpass)
        conn.autocommit = True
        try:
            rv = f(conn, *args, **kwargs)
        except Exception:
            raise
        finally:
            conn.close()
        return rv
    return pgconnect_

@pgconnect
def getneuronview(conn,neuronname):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    stmt = "SELECT * FROM neuronview WHERE name LIKE '{}'".format(neuronname)
    cur.execute(stmt)
    return cur.fetchall()


def escapechars(a_string):
    tdict = {
        "]":  "",
        "[":  "",
        "^":  "",
        "$":  ""
    }
    for item in tdict:
        a_string = a_string.replace(item, tdict[item])
    return a_string

@pgconnect
def getcurrentversion(conn,table):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    stmt = "SELECT * FROM {} WHERE active = true".format(table)
    cur.execute(stmt)
    return cur.fetchone()

@pgconnect
def getdataforsearch(conn):
    cur=conn.cursor()
    stmt = """
    select id, REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(concat(name,' ', age,' ', region_array,' ',celltype_array,' ', archive_name,' ', depositiondate,' ', uploaddate,' ', publication_journal,' ', publication_title,' ', publication_pmid,' ', publication_doi,' ', expcond_name,' ', magnification,' ', objective,' ', originalformat_name,' ', reconstruction,' ', png_url,' ', slicing_direction,' ', slicingthickness,' ', shrinkage,' ', shrinkagevalues,' ', age_scale,' ', gender,' ', max_age,' ', min_age,' ', min_weight,' ', max_weight,' ', note,' ', staining_name,' ', protocol,' ', strain_name,' ', species_name,' ', structural_domain),'"',''),']',''),'[',''),'{',''),'}',''),',',' ') as allt, name
from neuronview
    """
    cur.execute(stmt)
    res = cur.fetchall()
    return res


@pgconnect
def getdata(conn,table,keyvals,orderby ='',limval=1):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if orderby != '':
        orderby = 'ORDER BY {}'.format(orderby)
    whereclause = [item + '=' + keyvals[item] for item in keyvals]
    if len(whereclause) > 0:
        whereclause = 'WHERE {}'.format(','.join(whereclause))
    else:
        whereclause = ''
    stmt = 'SELECT * FROM {} {} {} LIMIT {}'.format(table,whereclause,orderby,limval)
    cur.execute(stmt)
    res = cur.fetchall()
    return res
    
@pgconnect
def getpvec(conn,neuron_id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('select * from pvec where neuron_id ={}'.format(neuron_id))
    res = cur.fetchall()
    if res:
        result = dict(res[0])
    else:
        result = {}
    return result   

@pgconnect
def getrowasdict(conn,table,id):
    statement = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name   = '{}'""".format(table)
    cur = conn.cursor()
    cur.execute(statement)
    result = cur.fetchall()
    cols = [item[0] for item in result]
    statement = "SELECT {} from {} where {}.id = {}".format(','.join(cols),table,table,id)
    cur.execute(statement)
    result = cur.fetchone()
    if result is None:
        return None
    else:
        #resdict =  dict(zip(cols,result))
        resdict =  {table + '_' + key: val for key,val in zip(cols,result)}
        return resdict

@pgconnect
def getmycelltypes(conn,path):
    if path is not None:
        statement = "select name from celltype where path @> '{}' order by path".format(path)
        cur = conn.cursor()
        cur.execute(statement)
        res = cur.fetchall()
    else:
        res = []
    result = {}
    typelabels = ['class1','class2','class3','class3B','class3C']
    defaultval = ['Not reported'] * 5
    if len(typelabels) < len(res):
        lendiff = len(res) - len(typelabels)
        typelabels = typelabels + ['class3C'] * lendiff
        defaultval = defaultval + ['Not reported'] * lendiff
    result = [[a,b] for a,b in zip(typelabels,defaultval)]
    for ix in range(len(res)):
        result[ix][1] = res[ix][0]
    resultdict = {item[0]: item[1] for item in result if item[0 != 'class3C']}
    if len(res) > 4:
        resultdict['class3C'] = res[4][0]

    return { "celltypelabels": result,**resultdict}



def cleanstr(astring):
    if astring[0] == " ":
        astring = astring[1:]
    astring = astring.replace(' ','_')
    return "".join([c for c in astring if c.isalpha() or c.isdigit() or c == '_']).rstrip()

def cleanerr(astring):
    return "".join([c for c in astring if c.isalpha() or c.isdigit() or c == '_' or c == ' ']).rstrip()

def cleanval(astring):
    return astring.replace(',','')

@pgconnect
def insert(conn,tablename,data):
    # takes data with fields as keys in dictionary, data as values
    cur = conn.cursor()
    # clean 'NULL' Values
    values = ''
    data = {item: data[item] for item in data if data[item] is not None } 
    data = {item: data[item] for item in data if data[item] != 'NULL'}
    
        
    for item in data:
        if isinstance(data[item],str):
            values += "'{}',".format(data[item].replace("'","''"))
        else:
            values += str(data[item]) + ','
    values = values[:-1]
    
    fields = ",".join(data.keys())
    if len(data) == 0:
        statement = "INSERT INTO {}(id) VALUES(DEFAULT)".format(tablename)
    else:
        statement = """INSERT INTO {}({}) VALUES ({}) """.format(tablename,fields,values)
    cur.execute(statement)  
    cur.execute("SELECT currval(pg_get_serial_sequence('{}','id'))".format(tablename))
    result = cur.fetchone()
    inserted_id = result[0]
    conn.close()
    return inserted_id


@pgconnect
def isindb(conn,tablename, column, value):
    # check if value in table of specified column is in db
    value = value.replace("'","''")
    cur = conn.cursor()
    statement = "SELECT {} FROM {} where {} = '{}'".format(column,tablename,column,value)
    try:
        cur.execute(statement)
    except Exception as e:
        print(e)
    result = cur.fetchone()
    return result is not None

def stq(tocheck):
    if isinstance(tocheck,str):
        return "'{}'".format(tocheck)
    else: 
        return str(tocheck)

@pgconnect
def update(conn,tablename,whereq,updateq):
    """ Updates table with rows matching whereq to values of updateq
    Returns numbers of rows affected, -1 if none
    """
    wclause = " AND ".join([item + " = " + stq(whereq[item]) for item in whereq])
    uclause = ", ".join([item + " = " + stq(updateq[item]) for item in updateq])
    cur = conn.cursor()
    statement = "UPDATE {} SET {} WHERE {}".format(tablename,uclause,wclause)
    cur.execute(statement)
    return cur.rowcount


@pgconnect
def getnneurons(conn,foldername):
    archive_name = io.namefromfolder(foldername)
    cur = conn.cursor()
    stmt = """
    SELECT 
    COUNT(public.neuron.id) AS nneurons, 
    public.archive.name 
FROM 
    public.neuron 
INNER JOIN 
    public.archive 
ON 
    ( 
        public.neuron.archive_id = public.archive.id) 
WHERE 
    public.archive.name = '{}' 
GROUP BY 
    public.archive.name""".format(archive_name)
    cur.execute(stmt)
    res = cur.fetchone()
    if res is None:
        return 0
    else:
        return res[0]

@pgconnect
def deleteneuron(conn,neuronname):
    """
    Delete neuron from project DB
    """
    cur = conn.cursor()
    stmt = "delete from ingestion where neuron_name='{}'".format(neuronname)
    cur.execute(stmt)
    stmt = "delete from neuron where name='{}'".format(neuronname)
    cur.execute(stmt)

@pgconnect
def getpvecmes(conn,neuron_id):
    def zeroifnone(a):
        if a is None:
            return 0 
        else:
            return a
    # produces vector of pvec + summary measurements (length 121) for duplicate detection
    cur = conn.cursor()
    stmt = "select summary_meas_id from neuron where id={}".format(neuron_id)
    cur.execute(stmt)
    mesid = cur.fetchone()[0]
    stmt = "SELECT * from measurements where id ={}".format(mesid)
    cur.execute(stmt)
    measurements = list(cur.fetchone())[1:]
    measurements = [zeroifnone(item) for item in measurements]
    stmt = "select coeffs from pvec where neuron_id={}".format(neuron_id)
    cur.execute(stmt)
    res = cur.fetchone()
    persistence = res[0]

    return (measurements,persistence)    

@pgconnect
def ingestdomain(conn,neuron_id,domains,morph_attr):
    cur = conn.cursor()
    if "Soma" in domains:
        del domains["Soma"]
    for key in domains:
        stmt = "INSERT INTO neuron_structure (neuron_id, completeness, domain,morph_attributes) VALUES ({},'{}','{}',{})".format(neuron_id,domains[key],key,morph_attr)
        cur.execute(stmt)




@pgconnect
def getneuronfolder(conn,neuron_name):
    # get archive of ready neuron names
    cur = conn.cursor()

    statement = "SELECT foldername FROM ingested_archives,ingestion WHERE ingested_archives.name = ingestion.archive AND ingestion.neuron_name = '{}' order by ingested_archives.date desc limit 1".format(neuron_name.replace("'","''"))
    cur.execute(statement)
    result = cur.fetchone()
    res = result[0]
    return res

@pgconnect
def getfolderfromname(conn,archive_name):
    # get archive of ready neuron names
    cur = conn.cursor()

    statement = "SELECT foldername FROM ingested_archives WHERE ingested_archives.name = '{}' ORDER BY ingested_archives.date desc limit 1".format(archive_name)
    cur.execute(statement)
    result = cur.fetchone()
    res = result[0]
    return res

@pgconnect
def getneuronarchive(conn,neuron_name):
    # get archive of ready neuron names
    cur = conn.cursor()

    statement = "SELECT archive FROM ingestion WHERE ingestion.neuron_name = '{}'".format(neuron_name.replace("'","''"))
    cur.execute(statement)
    result = cur.fetchone()
    res = result[0]
    return res


@pgconnect
def getarchiveneurons(conn,archive):
    cur = conn.cursor()
    statement = "SELECT neuron.name,neuron.id from neuron,ingestion where neuron.name = ingestion.neuron_name AND ingestion.archive = '{}'".format(archive)
    cur.execute(statement)
    res = cur.fetchall()
    resultnames = [item[0] for item in res]
    resultids = [item[1] for item in res]
    return (resultnames,resultids)

@pgconnect
def getarchivemeasurements(conn,archive):
    cur = conn.cursor()
    statement = "SELECT neuron.summary_meas_id from neuron,ingestion where neuron.name = ingestion.neuron_name AND ingestion.archive = '{}'".format(archive)
    cur.execute(statement)
    res = cur.fetchall()
    resultids = [item[0] for item in res]
    return resultids

@pgconnect
def pginsert(conn,tablename,data):
    """
    Generic function, inserts data values defined as key-value pairs into named table  
    """
    cur = conn.cursor()
    data = {item: data[item] for item in data if data[item] is not None}
    fields = ",".join(data.keys())
    values = "','".join([str(item).replace("'","''") for item in data.values()])
    statement = """INSERT INTO {}({}) VALUES ('{}') """.format(tablename,fields,values)
    cur.execute(statement)  
    cur.execute("select currval('{}_id_seq')".format(tablename))
    result = cur.fetchone()
    inserted_id = result[0]
    return inserted_id
