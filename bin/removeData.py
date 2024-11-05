#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Remove data and any record of them from the system. This can be just a corrupted file or an entire
# dataset.
#
# v1.0                                                                                  Apr 28, 2017
#---------------------------------------------------------------------------------------------------
import sys,os,subprocess,getopt,time
from scheduler import Scheduler
import MySQLdb

BASE = os.getenv('KRAKEN_SE_BASE')
BASE_LOGS = os.getenv('KRAKEN_AGENTS_LOG')
BASE_WEBP = os.getenv('KRAKEN_AGENTS_WWW')
if BASE == "" or BASE_LOGS == "" or BASE_WEBP == "":
    print(" ERROR - KRAKEN not fully initialized?")
    sys.exit(1)


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
        print(' select: ' + sql)

    results = []
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print('ERROR(%s) - could not find request id.'%(sql))

    # found the request Id
    for row in results:
        if debug>1:
            print(' FileName: %s  NEvents: %d'%(row[0],int(row[1])))
        files.append(row[0])

    return files

def getDatasetId(process,setup,tier,cursor,debug):
    # Find the dataset id for this dataset to facilitate further queries

    # start with an invalid Id
    datasetId = -1

    sql = "select DatasetId from Datasets where " \
        + "DatasetProcess='%s' and DatasetSetup='%s' and DatasetTier='%s';"%(process,setup,tier)
    if debug>0:
        print(' select: ' + sql)
    results = []
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print(" Error (%s): unable to fetch data."%(sql))
        sys.exit(0)
    
    if len(results) <= 0:
        print(' Requested dataset not defined, check database (nEntries=%d).'%(len(results)))
        sys.exit(0)
    elif len(results) > 1:
        print(' Requested dataset not well defined, check database (nEntries=%d).'%(len(results)))
        sys.exit(0)
    else:
        datasetId = int(results[0][0])
        if debug>0:
            print(' DatasetId=%d.'%(datasetId))

    return datasetId

def getRequestIds(datasetId,config,version,cursor,debug):
    # extract the unique request id for this piece of data

    requestIds = []
    pys = []
    sql = "select RequestId, RequestPy from Requests where DatasetId=%d"%(datasetId) \
        + " and RequestConfig='%s' and RequestVersion='%s'"%(config,version)
    if debug>0:
        print(' select: ' + sql)

    results = []
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print('ERROR(%s) - could not find request id.'%(sql))

    # found the request Id
    for row in results:
        requestIds.append(int(row[0]))
        pys.append(str(row[1]))
        
    return requestIds,pys

def remove(dataset,config,version,dbs,exe):
    # remove the full dataset and database info

    print(f" Dataset: {dataset}")

    # make sure to get dataset convention right
    if dataset[0] != '/':
        dataset = '/' + dataset.replace('+','/')

    # Decompose dataset into the three pieces (process, setup, tier)
    f = dataset.split('/')
    if len(f) < 4:
        return
    process = f[1]
    setup   = f[2]
    tier    = f[3]

    # Find the dataset id and request id
    datasetId = getDatasetId(process,setup,tier,cursor,debug)
    requestIds, pys = getRequestIds(datasetId,config,version,cursor,debug)

    # notify about several pys found
    if len(requestIds)>1:
        print(" ERROR -- multiple request ids with different pys found")
        for reqId,py in zip(requestIds, pys):
            print(f" ReqId: {reqId}; Py: {py};")
        sys.exit(-1)
    
    # Loop through the request Ids
    for reqId,py in zip(requestIds, pys):
        print(' Ids: dataset=%d  request=%d;  Py=%s;'%(datasetId,reqId,py))
        if reqId < 0:
            print(' ERROR - no request id was found to match request. (Python config correct?)')
            sys.exit(1)
        
        # Is this a complete dataset?
        if fileName == '':
            print(' Deletion of a complete dataset requested.')
        
        # Show all files to remove
        fileList = findFiles(reqId,fileName,cursor,debug)
        
        # Remove all running jobs
        removeCondorJobs(config,version,process,setup,tier,exe,debug)

        # Remove the files and all records of them
        if fileName == '':
            removeDataset(process,setup,tier,datasetId,reqId,config,version,py,exe)
        else:
            removeFiles(fileList,process,setup,tier,datasetId,reqId,config,version,exe)
    
        # Re-generate the catalog after the deletion
        cmd = 'generateCatalogs.py %s/%s %s'%(config,version,dataset)
        print(' ctg: %s'%(cmd))
        if exe:
            os.system(cmd)
    
def removeCondorJobs(config,version,process,setup,tier,exe,debug):
    # Remove the condor jobns related with this dataset

    # Find all running jobs
    clusterIds = ""
    cmd = 'condor_q -format "%d" ClusterId -format " %s\n" Args| cut -d " " -f 1,6 |sort -u'
    scheduler = Scheduler()
    (rc,out,err) = scheduler.executeCondorCmd(cmd,False)
    ds = process+'+'+setup+'+'+tier
    for line in out.split('\n'):
        if ds in line and version in line and config in line:
            clusterIds = clusterIds + " " + line.split(' ')[0]
    if clusterIds != "":
        print(" Running jobs: " + clusterIds)
        if exe == True:
            print(" Removing condor jobs")        
            scheduler.executeCondorCmd('condor_rm ' + clusterIds,True)
    else:
        print(" No running jobs found.")
    return
    
def removeVersionIfEmpty(config,version,exe,debug):
    # Show all files related with the given request id
    cmd = f"list {BASE}/{config}/{version} 2> /dev/null"
    if debug>0:
        print(' Listing directory: ' + cmd)
    dataset = ""
    for line in os.popen(cmd).readlines():  # run command
        dataset = line[:-1].split('/')[-1]
        if debug>0:
            print(f" Found dataset: {dataset}")

    if dataset == "":
        print(f" Empty directory identified for deletion: {BASE}/{config}/{version}")
        if exe:
            cmd = f"removedir {BASE}/{config}/{version}"
            print(' Removing empty directory: ' + cmd)        
            os.system(cmd)
            cmd = f"rm -r {BASE_LOGS}/reviewd/{config}/{version} {BASE_WEBP}/reviewd/{config}/{version}"
            print(' Removing obsolete version: ' + cmd)        
            os.system(cmd)
    else:
        print(f" Directory not empty: NO DELETION ({config}/{version})")
        
    return
    
def removeFiles(fileList,process,setup,tier,datasetId,requestId,config,version,exe):
    # Delete thoroughly the given list of files from the disks (T2/3 and the database)

    dataset = process + '+' + setup + '+' + tier

    for file in fileList:

        fullFile = '%s/%s/%s/%s/%s.root'%(BASE,config,version,dataset,file)

        # delete from T2
        cmd = 't2tools.py --action=rm --source=%s'%(fullFile)
        print(' t2t: %s'%(cmd))
        if exe:
            os.system(cmd)
        
        ## delete from T3
        #cmd = 'ssh t3btch090.mit.edu hdfs dfs -rm %s'%(fullFile)
        #print(' loc: %s'%(cmd))
        # if exe:
        #    os.system(cmd)

        # delete from the database (for catalogs)
        sql  = "delete from Files where RequestId=%d and fileName='%s'"%(requestId,file)
        print(' sql: %s'%(sql))
        if exe:
            try:
                # execute the SQL command
                cursor.execute(sql)
            except:
                print(" Error (%s): unable to delete data."%(sql))

        return


def removeDataset(process,setup,tier,datasetId,requestId,config,version,py,exe):
    # Delete the given dataset from the disks (T2/3 and the database)

    dataset = process + '+' + setup + '+' + tier
    catalog = os.getenv('KRAKEN_CATALOG_OUTPUT')
    fullFile = '%s/%s/%s/%s'%(BASE,config,version,dataset)
    logs = f"{BASE_LOGS}/reviewd/{config}/{version}/{dataset}"
    webp = f"{BASE_WEBP}/reviewd/{config}/{version}/{dataset}"

    # delete from T2
    cmd = 'ssh paus@t2srv0017.cmsaf.mit.edu hdfs dfs -rm -r %s'%(fullFile)
    print(' t2t: %s'%(cmd))
    if exe:
        os.system(cmd)
        
    ## delete from T3
    #cmd = 'ssh t3btch090.mit.edu hdfs dfs -rm -r %s'%(fullFile)
    #print(' loc: %s'%(cmd))
    #if exe:
    #    os.system(cmd)

    # delete from the database (for catalogs)
    sql  = "delete from Files where RequestId=%d"%(requestId)
    print(' sql: %s'%(sql))
    if exe:
        try:
            # Execute the SQL command
                cursor.execute(sql)
        except:
            print(" Error (%s): unable to delete data."%(sql))

    cmd = 'rm -rf %s/%s/%s/%s'%(catalog,config,version,dataset)
    print(' ctg: %s'%(cmd))
    if exe:
        os.system(cmd)

    # delete all logs and webpages
    cmd = f"rm -rf {logs} {webp}"
    print(' log: %s'%(cmd))
    if exe:
        os.system(cmd)

    
    # Remove the request from the request table
    cmd = 'addRequest.py --delete=1 --config=%s --version=%s --py=%s --dataset=%s'%\
        (config,version,py,dataset)
    print(' drq: %s'%(cmd))
    if exe:
        os.system(cmd)
    
    return

def testLocalSetup(config,version,dbs,delete,debug=0):
    # test all relevant components and exit is something is off

    # check the input parameters
    if config == '':
        print(' Error - no config specified. EXIT!\n')
        print(usage)
        sys.exit(1)
    if version == '':
        print(' Error - no version specified. EXIT!\n')
        print(usage)
        sys.exit(1)

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: removeData.py  --config=<name>\n"
usage += "                       --version=<name>\n"
usage += "                     [ --pattern='']\n"
usage += "                     [ --fileName='' ]\n"
usage += "                     [ --debug=0 ]\n"
usage += "                     [ --exec (False) ]\n"
usage += "                     [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['fileName=','pattern=','config=','version=','debug=','exec','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
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

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--fileName":
        fileName = arg
    if opt == "--pattern":
        pattern = arg
    if opt == "--config":
        config = arg
    if opt == "--version":
        version = arg
    if opt == "--exec":
        exe = True
    if opt == "--debug":
        debug = int(arg)

# make sure the request makes sense
testLocalSetup(config,version,dbs,delete,debug)

# get access to the database
(db,cursor) = db()

datasets = []
cmd = 'list ' + BASE + '/' + config + '/' + version + ' 2> /dev/null'
print(' Listing: ' + cmd)
for line in os.popen(cmd).readlines():  # run command
    f = line[:-1].split('/')
    if len(f)<2:
        print(f" No valid dataset found (line: {line[:-1]}).")
        sys.exit(2)
    dataset = f[-1]
    if debug>1:
        print(' Sample(%s): '%(pattern) + dataset)
    if pattern in dataset:
        datasets.append(dataset)
        
## there was no match, use the pattern itself as the only dataset
## --> this should actually never happen because the dataset name will match itself
if len(datasets)==0:
    print(" INFO -- No matching dataset found.")
#    print(" No match found, try explicit pattern: %s."%(pattern))
#    datasets.append(pattern)


# loop over all datasets identified 
for dataset in datasets:
    if debug>-1:
        print(' -o-o-o-o- Deleting -o-o-o-o-  ' + dataset)

    # remove the specific dataset
    remove(dataset,config,version,dbs,exe)

removeVersionIfEmpty(config,version,exe,debug)
    
db.close()
