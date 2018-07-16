#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------
# Remove data and any record of them from the system. This can be just a corrupted file or an entire
# dataset.
#
# v1.0                                                                                  Apr 28, 2017
#---------------------------------------------------------------------------------------------------
import sys,os,subprocess,getopt,time
import MySQLdb

from scheduler import Scheduler
from lfn import Lfn

BASE = os.getenv('KRAKEN_SE_BASE')

def db():
    # Get our access to the database

    # Open database connection
    db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
    # Prepare a cursor object using cursor() method
    cursor = db.cursor()

    return (db,cursor)

def getDatasetId(process,setup,tier,cursor,debug):
    # Find the dataset id for this dataset to facilitate further queries

    # start with an invalid Id
    datasetId = -1

    sql = "select DatasetId from Datasets where " \
        + "DatasetProcess='%s' and DatasetSetup='%s' and DatasetTier='%s';"%(process,setup,tier)
    if debug>0:
        print ' select: ' + sql
    results = []
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " Error (%s): unable to fetch data."%(sql)
        sys.exit(0)
    
    if len(results) <= 0:
        print ' Requested dataset not defined, check database (nEntries=%d).'%(len(results))
        sys.exit(0)
    elif len(results) > 1:
        print ' Requested dataset not well defined, check database (nEntries=%d).'%(len(results))
        sys.exit(0)
    else:
        datasetId = int(results[0][0])
        if debug>0:
            print ' DatasetId=%d.'%(datasetId)

    return datasetId

def getRequestId(datasetId,config,version,cursor,debug):
    # extract the unique request id for this piece of data

    requestId = -1
    sql = "select RequestId from Requests where DatasetId=%d"%(datasetId) \
        + " and RequestConfig='%s' and RequestVersion='%s'"%(config,version)
    if debug>0:
        print ' select: ' + sql

    results = []
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print 'ERROR(%s) - could not find request id.'%(sql)

    # found the request Id
    for row in results:
        requestId = int(row[0])

    return requestId

def remove(lfn,exe):
    # remove this lfn from disk, bambu and dynamo databases

    # Decompose dataset into the three pieces (process, setup, tier)
    f = lfn.dataset.split("+")
    process = f[0]
    setup   = f[1]
    tier    = f[2]

    # Find the dataset id and request id
    datasetId = getDatasetId(process,setup,tier,cursor,debug)
    requestId = getRequestId(datasetId,lfn.config,lfn.version,cursor,debug)

    print ' Ids: dataset=%d  request=%d'%(datasetId,requestId)
    if requestId < 0:
        print ' ERROR - no request id was found to match your request. (Is your python config correct?)'
        sys.exit(1)

    removeFile(lfn,requestId)
    
    # Re-generate the catalog after the deletion
    cmd = 'generateCatalogs.py %s/%s %s'%(lfn.config,lfn.version,lfn.dataset)
    print ' ctg: %s'%(cmd)
    if exe:
        os.system(cmd)
    
def removeFile(lfn,requestId):
    # Delete thoroughly the given file from the disks (T2/3 and the database)

    # delete from T2
    cmd = 't2tools.py --action=rm --source=/cms/%s'%(lfn.lfn)
    print ' t2t: %s'%(cmd)
    if exe:
        os.system(cmd)
    
    # delete from T3
    cmd = 'hdfs dfs -rm /cms/%s'%(lfn.lfn)
    print ' loc: %s'%(cmd)
    if exe:
        os.system(cmd)

    # delete from the database (for catalogs)
    sql  = "delete from Files where RequestId=%d and fileName='%s'"%(requestId,lfn.fileId)
    print ' sql: %s'%(sql)
    if exe:
        try:
            # Execute the SQL command
            cursor.execute(sql)
        except:
            print " Error (%s): unable to delete data."%(sql)

    # delete from dynamo
    cmd = "dynamo-delete-one-file %s"%(lfn.lfn)
    print ' dyn: %s'%(cmd)
    if exe:
        os.system(cmd)


#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: removeData.py  --fileName='' \n"
usage += "                     [ --debug=0 ]\n"
usage += "                     [ --exec (False) ]\n"
usage += "                     [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['fileName=','debug=','exec','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# Set defaults for each command line parameter/option
debug = 0
exe = False
fileName = ''

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--fileName":
        fileName = arg
    if opt == "--exec":
        exe = True
    if opt == "--debug":
        debug = int(arg)

# get access to the database
(db,cursor) = db()

fileLfn = Lfn(fileName)
fileLfn.show()

# remove the specific dataset
remove(fileLfn,exe)

db.close()
