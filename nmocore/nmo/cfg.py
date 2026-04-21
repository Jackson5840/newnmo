import os 

datapath = '/data/nmo-are/archives/'
metapath = '/data/nmo-are/metadata/'
scrollpath = '/data/nmo-are/scrollimages/'

# Definition file
#readyarchives = os.path.join(remotepath,'readyarchives.csv')
readyarchives = os.path.join(datapath,'readyarchives.csv')


# Postgres config
dbhost = os.environ.get("POSTGRES_HOST", "db")
redishost = os.environ.get("REDIS_HOST", "cache")
dbsel = os.environ.get("POSTGRES_DB", "nmo")
dbuser = os.environ.get("POSTGRES_USER", "nmo")
dbpass = os.environ.get("POSTGRES_PASSWORD", "")

mysql_host = os.environ.get("MYSQL_HOST", "localhost")
mysql_user = os.environ.get("MYSQL_USER", "root")
mysql_password = os.environ.get("MYSQL_PASSWORD", "")
mysql_db = os.environ.get("MYSQL_DB", "nmo")