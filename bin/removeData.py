#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Remove data and any record of them from the system. This can be just a corrupted file or an entire
# dataset.
#
# Include dynamo deletions (per file or per dataset)
#
# v1.0                                                                                  Apr 28, 2017
#---------------------------------------------------------------------------------------------------
import sys,os,subprocess,getopt,time
from scheduler import Scheduler
import MySQLdb

BASE = os.getenv('KRAKEN_SE_BASE')

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
        if debug>0:
            print ' FileName: %s  NEvents: %d'%(row[0],int(row[1]))
        files.append(row[0])

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

def remove(dataset,config,version,dbs,py,exe):
    # remove the full dataset and database info

    # make sure to get dataset convention right
    if dataset[0] != '/':
        dataset = '/' + dataset.replace('+','/')

    # Decompose dataset into the three pieces (process, setup, tier)
    f = dataset.split('/')
    process = f[1]
    setup   = f[2]
    tier    = f[3]
    
    # Find all running jobs
    clusterIds = ""
    if exe == True:
        cmd = 'condor_q -format "%d" ClusterId -format " %s\n" Args| cut -d " " -f 1,6 |sort -u'
        scheduler = Scheduler()
        (rc,out,err) = scheduler.executeCondorCmd(cmd,False)
        ds = process+'+'+setup+'+'+tier
        for line in out.split('\n'):
            if ds in line and version in line and config in line:
                clusterIds = clusterIds + " " + line.split(' ')[0]
        if clusterIds != "":
            print " Running jobs: " + clusterIds
        else:
            print " No running jobs found."

    # Find the dataset id and request id
    datasetId = getDatasetId(process,setup,tier,cursor,debug)
    requestId = getRequestId(datasetId,config,version,py,cursor,debug)
    print ' Ids: dataset=%d  request=%d'%(datasetId,requestId)
    if requestId < 0:
        print ' ERROR - no request id was found to match request. (Python config correct?)'
        sys.exit(1)
    
    # Is this a complete dataset?
    if fileName == '':
        print ' Deletion of a complete dataset requested.'
    
    # Show all files to remove
    fileList = findFiles(requestId,fileName,cursor,debug)
    
    if exe == True:
    
        # Remove all running jobs
        if clusterIds != "":
            scheduler.executeCondorCmd('condor_rm ' + clusterIds,True)

        # Remove the files and all records of them
        if fileName == '':
            
            removeDataset(process,setup,tier,datasetId,requestId,config,version)

            # Remove the request from the request table
            cmd = 'addRequest.py --delete=1 --config=%s --version=%s --py=%s --dataset=%s'%\
                (config,version,py,dataset)
            print ' drq: %s'%(cmd)
            os.system(cmd)

        else:
            removeFiles(fileList,process,setup,tier,datasetId,requestId,config,version)
    
        # Re-generate the catalog after the deletion
        cmd = 'generateCatalogs.py %s/%s %s'%(config,version,dataset)
        print ' ctg: %s'%(cmd)
        os.system(cmd)
        
    else:
        print ' To execute please add --exec option\n'
    
def removeFiles(fileList,process,setup,tier,datasetId,requestId,config,version):
    # Delete thoroughly the given list of files from the disks (T2/3 and the database)

    dataset = process + '+' + setup + '+' + tier

    for file in fileList:

        fullFile = '%s/%s/%s/%s/%s.root'%(BASE,config,version,dataset,file)

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
            # execute the SQL command
            cursor.execute(sql)
        except:
            print " Error (%s): unable to delete data."%(sql)

        ## delete meta data from Dynamo
        #cmd = 'dynamo-delete-one-file %s'%(fullFile)
        #print ' logs: %s'%(cmd)
        #os.system(cmd)


def removeDataset(process,setup,tier,datasetId,requestId,config,version):
    # Delete the given dataset from the disks (T2/3 and the database)

    dataset = process + '+' + setup + '+' + tier
    catalog = '/home/cmsprod/catalog/t2mit'
    fullFile = '%s/%s/%s/%s'%(BASE,config,version,dataset)
    logs = '/local/cmsprod/Kraken/agents/reviewd/%s/%s/%s'%(config,version,dataset)

    # delete from T2
    cmd = 'ssh paus@t2srv0017.cmsaf.mit.edu hdfs dfs -rm -r %s'%(fullFile)
    print ' t2t: %s'%(cmd)
    os.system(cmd)
        
    # delete from T3
    cmd = 'hdfs dfs -rm -r %s'%(fullFile)
    print ' loc: %s'%(cmd)
    os.system(cmd)

    # delete from the database (for catalogs)
    sql  = "delete from Files where RequestId=%d"%(requestId)
    print ' sql: %s'%(sql)
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print " Error (%s): unable to delete data."%(sql)

    cmd = 'rm -rf %s/%s/%s/%s'%(catalog,config,version,dataset)
    print ' ctg: %s'%(cmd)
    os.system(cmd)

    # delete all logs
    cmd = 'rm -rf %s'%(logs)
    print ' logs: %s'%(cmd)
    os.system(cmd)

    ## delete meta data from Dynamo
    #cmd = 'dynamo-delete-dataset %s/%s/%s'%(config,version,dataset)
    #print ' logs: %s'%(cmd)
    #os.system(cmd)

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
usage += " Usage: removeData.py  --pattern=<name>\n"
usage += "                       --config=<name>\n"
usage += "                       --version=<name>\n"
usage += "                       --py=<name>\n"
usage += "                     [ --fileName='' ]\n"
usage += "                     [ --debug=0 ]\n"
usage += "                     [ --exec (False) ]\n"
usage += "                     [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['fileName=','pattern=','config=','version=','py=','debug=','exec','help']
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
pattern = ''
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
    if opt == "--pattern":
        pattern = arg
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
testLocalSetup(pattern,config,version,dbs,py,delete,debug)

# get access to the database
(db,cursor) = db()

datasets = []
cmd = 'list ' + BASE + '/' + config + '/' + version + ' 2> /dev/null'
print ' Listing: ' + cmd
for line in os.popen(cmd).readlines():  # run command
    dataset = line[:-1].split('/')[-1]
    if debug>1:
        print ' Sample(%s): '%(pattern) + dataset
    if pattern in dataset:
        datasets.append(dataset)

for dataset in datasets:
    if debug>-1:
        print ' -o-o-o-o- Deleting -o-o-o-o-  ' + dataset

    # remove the specific dataset
    remove(dataset,config,version,dbs,py,exe)

db.close()
