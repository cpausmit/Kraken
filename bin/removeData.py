#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------
# Remove data and any record of them from the system. This can be just a corrupted file or an entire
# dataset.
#
# v1.0                                                                                  Apr 28, 2017
#---------------------------------------------------------------------------------------------------

##/mnt/hadoop/cms/store/user/paus/pandaf/003/ZNuNuGJets_MonoPhoton_PtG-130_TuneCUETP8M1_13TeV-madgraph+RunIISummer16MiniAODv2-PUMoriond17_80X_mcRun2_asymptotic_2016_TrancheIV_v6-v1+MINIAODSIM/E84DBC18-70C9-E611-80CB-0025905A4964.root

import sys,os,subprocess,getopt,time
import MySQLdb

def db():
    # Get our access to the database

    # Open database connection
    db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
    # Prepare a cursor object using cursor() method
    cursor = db.cursor()

    return (db,cursor)

def findFiles(requestId,fileName,cursor,debug):
    # Show all files related with the given request id

    files = []

    sql = "select FileName, NEvents from Files where RequestId=%d"%(requestId)
    if fileName != '':
        sql += " and FileName like '%%%s%%'"%(fileName)
        
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
        print ' FileName: %s  NEvents: %d'%(row[0],int(row[1]))
        files.append(row[0])

    print ''

    return files

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

def getRequestId(datasetId,config,version,py,cursor,debug):
    # extract the unique request id for this piece of data

    requestId = -1
    sql = "select RequestId from Requests where DatasetId=%d"%(datasetId) \
        + " and RequestConfig='%s' and RequestVersion='%s' and RequestPy='%s'"%(config,version,py)
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

def removeFileEntries(fileList,process,setup,tier,datasetId,requestId,config,version):
    # Delete thoroughly the given list of files from the disks (T2/3 and the database)

    base = '/cms/store/user/paus'
    dataset = process + '+' + setup + '+' + tier

    for file in fileList:

        fullFile = '%s/%s/%s/%s/%s.root'%(base,config,version,dataset,file)

        # delete from T2
        cmd = 't2tools.py --action=rm --source=%s'%(fullFile)
        print ' t2t: %s'%(cmd)
        os.system(cmd)
        
        # delete from T3
        cmd = 'hdfs dfs -rm %s'%(fullFile)
        print ' loc: %s'%(cmd)
        os.system(cmd)

        # delete from the database (for catalogs)
        sql  = "delete from Files where RequestId=%d and fileName='%s'"%(requestId,file)
        print ' sql: %s'%(sql)
        try:
            # Execute the SQL command
            cursor.execute(sql)
        except:
            print " Error (%s): unable to delete data."%(sql)

    # regenerate the catalog after the deletion
    print ' generateCatalogs.py %s/%s %s'%(config,version,dataset)


def testLocalSetup(dataset,config,version,dbs,py,delete,debug=0):
    # test all relevant components and exit is something is off

    # check the input parameters
    if dataset == '':
        print ' Error - no dataset specified. EXIT!\n'
        print usage
        sys.exit(1)
    if config == '':
        print ' Error - no config specified. EXIT!\n'
        print usage
        sys.exit(1)
    if version == '':
        print ' Error - no version specified. EXIT!\n'
        print usage
        sys.exit(1)
    if py == '':
        print ' Error - no py specified. EXIT!\n'
        print usage
        sys.exit(1)

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: removeData.py  --dataset=<name>\n"
usage += "                       --config=<name>\n"
usage += "                       --version=<name>\n"
usage += "                       --py=<name>\n"
usage += "                     [ --fileName='' ]\n"
usage += "                     [ --debug=0 ]\n"
usage += "                     [ --exec (False) ]\n"
usage += "                     [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['fileName=','dataset=','config=','version=','py=','debug=','exec','help']
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
delete = 0
fileName = ''
dataset = ''
config = ''
version = ''
dbs = 'prod/global'
py = 'mc'

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--fileName":
        fileName = arg
    if opt == "--dataset":
        dataset = arg
        if dataset[0] != '/':
            dataset = '/' + dataset.replace('+','/')
    if opt == "--config":
        config = arg
    if opt == "--version":
        version = arg
    if opt == "--py":
        py = arg
    if opt == "--exec":
        exe = True
    if opt == "--debug":
        debug = int(arg)

# make sure the request makes sense
testLocalSetup(dataset,config,version,dbs,py,delete,debug)

# get access to the database
(db,cursor) = db()

# Decompose dataset into the three pieces (process, setup, tier)
f = dataset.split('/')
process = f[1]
setup   = f[2]
tier    = f[3]

# Find the dataset id
datasetId = getDatasetId(process,setup,tier,cursor,debug)
requestId = getRequestId(datasetId,config,version,py,cursor,debug)

print '\n Ids: dataset=%d  request=%d\n'%(datasetId,requestId)

# Show all files to remove
fileList = findFiles(requestId,fileName,cursor,debug)

if exe == True:
    # Remove the files and all records of them
    removeFileEntries(fileList,process,setup,tier,datasetId,requestId,config,version)
else:
    print ' To execute please add --exec option'

db.close()
