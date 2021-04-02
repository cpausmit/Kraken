#!/usr/bin/python
#===================================================================================================
# Add a new dataset into the Bambu database.
#
# v1.0                                                                                  Sep 19, 2014
#===================================================================================================
import sys,os,re,subprocess,getopt
import json
import MySQLdb
import rex
import fileIds

CATALOG_INPUT = os.environ.get('KRAKEN_CATALOG_INPUT','/home/cmsprod/catalog/t2mit')
WORK_DIR = os.environ.get('KRAKEN_WORK','/home/cmsprod/cms/jobs')

blockIds = {}
lfns = {}

def addBlock(datasetId,blockName):
    # add a new block of a given datasetId to the database

    sql  = "insert into Blocks(DatasetId,BlockName) values(%d,'%s')"%(datasetId,blockName)
    print(' ADDING--BLOCK--TO--DB. %s'%(sql))
    try:
        # Execute the SQL command
        cursor.execute(sql)
        db.commit()
        #print(' ADDED BLOCK TO DB. %s'%(sql))
    except:
        print(' ERROR (%s) - could not insert new block.'%(sql))
        print(" Unexpected error:", sys.exc_info()[0])
        pass

    bId = getBlockId(datasetId,blockName)
    print(" New BlockId: %d"%(bId))

    return bId

def addDetails(datasetId,lfns,debug=0):

    for lfn in lfns:
        if debug>0:
            print(" LFN -- " + lfn)
            print(" BlockId: %s"%(lfns[lfn].blockName))
        blockId = addBlock(datasetId,lfns[lfn].blockName)
        addLfn(datasetId,blockId,lfn,lfns[lfn].pathName,lfns[lfn].fileId.nEvents)
    return


def addLfn(datasetId,blockId,fileName,pathName,nEvents):
    # add an lfn to a given datasetId of a given blockId

    sql = "insert into Lfns(DatasetId,BlockId,FileName,PathName,NEvents) " \
        +  " values(%d,%d,'%s','%s',%d)"%(datasetId,blockId,fileName,pathName,nEvents)
    #print "Adding lfn: " + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        #print " success."
    except:
        #print ' ERROR (%s) - could not insert new file.'%(sql)
        #print " Unexpected error:", sys.exc_info()[0]
        pass

    return

def clearLocalCache(datasetId):

    cmd = 'rm -f %s/????/%s.????'%(WORK_DIR,datasetId)
    print ' Clearing cache: %s'%(cmd)

    myRex = rex.Rex()
    (rc,out,err) = myRex.executeLocalAction(cmd)

    return rc

def convertSizeToGb(sizeTxt):

    # first make sure string has proper basic format
    if len(sizeTxt) < 3:
        print ' ERROR - string for sample size (%s) not compliant. EXIT.'%(sizeTxt)
        sys.exit(1)

    if sizeTxt.isdigit(): # DAS decides to give back size in bytes
        sizeGb = int(sizeTxt)/1000./1000./1000.        
    else:              # DAS gives human readable size with unit integrated
        # this is the text including the size units, that need to be converted
        sizeGb  = float(sizeTxt[0:-2])
        units   = sizeTxt[-2:]
        # decide what to do for the given unit
        if   units == 'MB':
            sizeGb = sizeGb/1000.
        elif units == 'GB':
            pass
        elif units == 'TB':
            sizeGb = sizeGb*1000.
        else:
            print ' ERROR - Could not identify size. EXIT!'
            sys.exit(0)

    # return the size in GB as a float
    return sizeGb

def findDatasetProperties(dataset,dbsInst,debug=0):
    # test whether this is a legitimate dataset by asking DAS and determine size and number of files

    if "=" in dataset:                                      # this is a dataset produced with Kraken
        # find config, version and original dataset name
        f = dataset.split("=")
        conf = (f[0])[1:]
        vers = f[1]
        dset = f[2].replace("/","+")

        sizeGb = 10 # does not matter
        nFiles = 0

        cmd = 'cat %s/%s/%s/%s/Filesets'%(CATALOG_INPUT,conf,vers,dset)
        myRex = rex.Rex()
        (rc,out,err) = myRex.executeLocalAction(cmd)

        for line in out.split("\n"):
            line = ' '.join(line.split())
            f = line.split(" ")
            if len(f) > 1:
                nFiles += 1
                id = f[0]
                path = re.sub(r'root://.*/(/store/.*)',r'\1',f[1])
                lfn = "%s/%s.root"%(path,id)
                nEvents = int(f[2])

                fId = fileIds.fileId(id+".root",nEvents)
                lfn = fileIds.lfn(fId,id,path)
                lfns[fId.getName()] = lfn
                if debug>-1:
                    print " Adding: %s, %s, %s"%(id,lfn.fId.getName())

        return (sizeGb,nFiles,lfns)

    # dealing with a standard dataset first test
    if dbsInst == 'private':
        print(" Private dataset detected.")
        sizeGb = 10 # does not matter
        nFiles = 0
        f = dataset.split("/")
        trunc = f[1]
        conf = f[2]
        vers = f[3]
        dset = f[4]
        cmd = 'cat %s/%s/%s/%s/%s/RawFiles.00'%(CATALOG_INPUT,trunc,conf,vers,dset)
        print(" CMD: %s"%cmd)
        myRex = rex.Rex()
        (rc,out,err) = myRex.executeLocalAction(cmd)

        for line in out.split("\n"):
            #print(" LINE - >%s<"%(line))
            line = ' '.join(line.split())
            f = line.split(" ")
            if len(f) > 1:
                nFiles += 1
                id = (f[0].split('/')[-1]).replace('.root','')
                block = id[0:20]
                path = "/".join(f[0].split('/')[0:-1])
                path = re.sub(r'root://.*/(/store/.*)',r'\1',path)
                lfn = "%s/%s.root"%(path,id)
                #print(" ID: %s\nPATH %s\nLFN: %s"%(id,path,lfn))

                nEvents = int(f[2])

#            #print '%s: %d %d %f'%(fileName,nFiles,nEvents,totalSize/1000./1000./1000.)
#            fId = fileIds.fileId(fileName,nEvents)
#            lfn = fileIds.lfn(fId,block,path)
                fId = fileIds.fileId(id+".root",nEvents)
                lfn = fileIds.lfn(fId,block,path)
                #lfn.show()
                lfns[fId.getName()] = lfn
                if debug>-1:
                    print " Adding: %s, %s"%(id,path)
            else:
                pass
                #print(" LINE invalid")

        return (sizeGb,nFiles,lfns)

    # dealing with a standard dataset first test
    if not isDatasetValid(dataset,dbsInst,debug):
        print ' WARNING - dataset was not found to be valid.'
        print '         - continue and see whether it is in production.'
        print '         - to get all data this call has to be repeated'
        print '         - once the dataset is completed.'
        #return (-1,-1,-1)
    else:
        print ' INFO - dataset is valid.'

    proxy = getProxy()
    url = 'curl -s --cert %s -k -H "Accept: application/json"'%proxy \
        + ' "https://cmsweb.cern.ch/dbs/prod/global/DBSReader/'  \
        + 'files?dataset=%s&detail=true"'%(dataset)

    if debug>1:
        print ' CURL: ' + url

    myRex = rex.Rex()
    (rc,out,err) = myRex.executeLocalAction(url)

    if rc != 0:
        print ' ERROR ocurred in %s'%(url)
        sys.exit(1)

    data = json.loads(out)

    units = 'GB'
    nFiles = 0
    totalSize = 0
    blocks = []
    for entry in data:
        valid = int(entry["is_file_valid"])
        fileName = entry["logical_file_name"]
        path = "/".join(fileName.split("/")[:-1])
        size = int(entry["file_size"])
        block = entry["block_name"].split("#")[1]
        nEvents = int(entry["event_count"])
        if valid == 1:
            nFiles += 1
            totalSize += size
            #print '%s: %d %d %f'%(fileName,nFiles,nEvents,totalSize/1000./1000./1000.)
            fId = fileIds.fileId(fileName,nEvents)
            lfn = fileIds.lfn(fId,block,path)
            lfns[fId.getName()] = lfn

    try:
        sizeGb = convertSizeToGb(str(totalSize))
    except:
        print '\n Error - could not convert size and number of files (%s %s / %s).'\
            %(totalSize,units,nFiles)
        sys.exit(1)

    if debug>1:
        for lfn in lfns:
            lfns[lfn].show()


    print '\n DBS - %s --> %.1f %s (nFiles: %d)\n'%(dataset,sizeGb,units,nFiles)

    return (sizeGb, nFiles,lfns)

def getBlockIds(datasetId):

    sql = "select BlockId, BlockName from Blocks where " \
        + "DatasetId=%d;"%(datasetId)
    #print(" blockIds: %s"%(sql))

    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " ERROR (%s): unable to fetch data."%(sql)
        sys.exit(0)

    #print(" BlockId result")
    #print(results)

    for row in results:
        blockId = int(row[0])
        blockName = row[1]
        blockIds[blockName] = blockId

    return blockIds

def getBlockId(datasetId,blockName):
    # find the blockId for a given data block

    blockId = -1
    blockIds = getBlockIds(datasetId)
    blockId = blockIds[blockName]

    try:
        blockId = blockIds[blockName]
        return blockId
    except:
        pass
        print " ERROR (%s): blockName is not known."%(blockName)
        print " -----  ?because an entire new block was added and script does not allow it?"
        print " -----  number of blockIds: %d"%(len(blockIds))
        sys.exit(0)


    return blockId

def getDatasetId(dataset):
    # find the datasetId for a given dataset

    # Decompose dataset into the three pieces (process, setup, tier)
    f = dataset.split('+')
    process = f[0]
    setup   = f[1]
    tier    = f[2]

    sql = "select DatasetId from Datasets where " \
        + "DatasetProcess='%s' and DatasetSetup='%s' and DatasetTier='%s';"%(process,setup,tier)
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " Error (%s): unable to fetch data."%(sql)
        sys.exit(1)
    
    if len(results) != 1:
        print ' Dataset not in database. EXIT'
        sys.exit(1)
    else:
        datasetId = int(results[0][0])
 
    if datasetId<=0:
        print ' ERROR -- invalid dataset id: %d'%(datasetId)
        sys.exit(1)
            
    return datasetId

def getProxy():
    cmd = 'voms-proxy-info -path'
    for line in subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).stdout.readlines():
        proxy = line[:-1]
    
    return proxy

def insertDataset(db,process,setup,tier,dbsInst,sizeGb,nFiles,lfns,debug=0):
    
    # Prepare SQL query to INSERT a new record into the database.
    sql = "insert into Datasets(" \
        + "DatasetProcess,DatasetSetup,DatasetTier,DatasetDbsInstance,DatasetSizeGb,DatasetNFiles" \
        + ") values('%s','%s','%s','%s',%f,%d)"%(process,setup,tier,dbsInst,sizeGb,nFiles)
    
    if debug>-1:
        print ' insert: ' + sql

    try:
        # Execute the SQL command
        db.cursor().execute(sql)
        # Commit your changes in the database
        db.commit()
    except:
        print ' ERROR -- insert failed, rolling back.'
        # Rollback in case there is any error
        db.rollback()
        sys.exit(1)

    datasetId = getDatasetId(process+"+"+setup+"+"+tier)
    if debug>0:
        print(" Dataset id: %s"%(datasetId))
    blockIds = getBlockIds(datasetId);
    if debug>0:
        print(" Block Ids: ")
        print(blockIds)
    addDetails(datasetId,lfns,debug)

    return 0

def isDatasetValid(dataset,dbsInst,debug=0):
    # test whether this dataset is a valid dataset

    proxy = getProxy()
    url = 'curl -s --cert %s -k -H "Accept: application/json"'%proxy \
        + ' "https://cmsweb.cern.ch/dbs/prod/global/DBSReader/'  \
        + 'datasets?dataset_access_type=VALID&dataset=%s"'%(dataset)

    if debug>1:
        print(' CURL: ' + url)

    nTries = 0
    dbsList = 'FAKE CMSWEB Error FAKE'
    while 'CMSWEB Error' in dbsList and nTries < 4:

        if nTries>0 and debug>1:
            print(' CMSWEB error -- RETRY -- %d'%nTries)

        process = subprocess.Popen(url,stdout=subprocess.PIPE,shell=True)
        dbsList, error = process.communicate()

        if process.returncode != 0 or nTries > 2:
            print(" Received non-zero exit status: " + str(process.returncode))
            raise Exception(" ERROR -- Call to dbs failed, stopping!")

        nTries += 1

    if debug>1:
        print(' dbsList: ' + dbsList)

    datasetValid = True
    if dbsList == '[]':
        datasetValid = False

    return datasetValid

def removeDataset(db,datasetId,debug=0):

    cursor = db.cursor()

    # Prepare SQL query to REMOVE existing record from the database.
    sql = "delete from Requests where DatasetId=%d"%(datasetId)
    
    if debug>0:
        print(' delete: ' + sql)

    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print(' ERROR -- delete in Requests table failed.')
        sys.exit(1)

    sql = "delete from Datasets where DatasetId=%d"%(datasetId)

    if debug>0:
        print(' delete: ' + sql)

    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print ' ERROR -- delete in Datasets table failed.'
        sys.exit(1)

    return 0

def selectDataset(db,process,setup,tier,debug=0):

    # Prepare SQL query to SELECT existing record from the database.
    sql = "select * from Datasets where DatasetProcess='%s' and DatasetSetup='%s' "%(process,setup) \
        + "and DatasetTier='%s'"%(tier)

    cursor = db.cursor()

    if debug>0:
        print(' select: ' + sql)

    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print(" Error (%s): unable to fetch data."%(sql))
        sys.exit(0)

    return results

def testLocalSetup(dataset,dbsInst,debug=0):
    # test all relevant components and exit is something is off

    # check the user proxy
    rc = os.system("voms-proxy-info -exists")

    if debug > 0:
        print('Return code: %d'%(rc))

    if rc==0:
        if debug > 0:
            print(' User proxy is valid.')
    else:
        print(' Error - no valid proxy. EXIT!')
        sys.exit(1)

    # check the input parameters
    if dataset == '':
        print(' Error - no dataset specified. EXIT!\n')
        print(usage)
        sys.exit(1)

    # check basic dataset parameters
    if dataset[0] != '/':
        dataset = '/' + dataset.replace('+','/')

    f = dataset.split('/')
    if (len(f) != 4 and len(f) != 5 ) or f[0] != '':
        print('\n ERROR in dataset format. Please check dataset name.\n')
        print(usage)
        sys.exit(1)

    # if this is not a dataset in dbs
    if "=" in dataset:
        dbsInst = "local"

    return (dataset,dbsInst)

def updateDataset(db,process,setup,tier,sizeGb,nFiles,lfns,changed,debug=0):

    # Prepare SQL query to UPDATE existing record from the database.
    sql = "update Datasets set DatasetSizeGb=%f, DatasetNFiles=%d where "%(sizeGb,nFiles) + \
        " DatasetProcess='%s' and DatasetSetup='%s' and DatasetTier='%s'"%(process,setup,tier)

    cursor = db.cursor()

    if debug>0:
        print(" Sql: " + sql)

    try:
        # Execute the SQL command
        cursor.execute(sql)
        print(' database entry was updated.')
    except:
        print(' Error (%s) -- update failed.'%(sql))
        sys.exit(1)

    datasetId = getDatasetId(process+"+"+setup+"+"+tier)

    # make sure to add all relevant details to our database
    addDetails(datasetId,lfns)

    # make sure to clean the local cache files
    if changed:
        clearLocalCache(datasetId)

    return 0

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage =  " Usage: addDataset.py  --dataset=<name>\n"
usage += "                     [ --dbs='prod/global' ]\n"
usage += "                     [ --debug=0 ]\n"
usage += "                     [ --exec ]\n"
usage += "                     [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['dataset=','dbs=','debug=','exec','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# Set defaults for each command line parameter/option
debug = 0
dataset  = ''
dbsInst = 'prod/global'
exe = False

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--dataset":
        dataset = arg
    if opt == "--dbs":
        dbsInst = arg
    if opt == "--debug":
        debug = arg
    if opt == "--exec":
        exe = True

(dataset,dbsInst) = testLocalSetup(dataset,dbsInst,debug)

# Open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
# Prepare a cursor object using cursor() method
cursor = db.cursor()

# Decompose dataset into the three pieces (process, setup, tier)
f = dataset.split('/')
if len(f) == 4:
    process = f[1]
    setup   = f[2]
    tier    = f[3]
else:
    print(" Non standard dataset! Privately produced.")
    dbsInst  = 'private'
    process = f[2]
    setup   = f[3]
    tier    = f[4]

# First check whether this dataset already exists in the database
results = selectDataset(db,process,setup,tier,debug)
if debug>0:
    print(" Selected dataset:")
    print(results)

# Check the dataset in dbs
(sizeGb, nFiles, lfns) = findDatasetProperties(dataset,dbsInst,debug)

if sizeGb < 0:
    print ' Dataset does not exist or is invalid (%s).'%dataset
    if len(results) > 0:
        print ' Dataset was found in Bambu database. (nResults=%d)'%(len(results))
        rc = 0
        for row in results:
            datasetId = int(row[0])
            if exe:
                rc = removeDataset(db,datasetId,debug)
            else:
                print ' not removing dataset: use --exec option'
        if rc == 0:
            print ' Invalid dataset successfully removed from Bambu database (%s).'%(dataset)
        else:
            print ' Error removing invalid dataset from Bambu database (%s).'%(dataset)
    sys.exit(0)

# Dataset is valid now see what remains to be done
if len(results) == 1:
    print ' Dataset exists in database. Will try to update properties.\n'
    for row in results:
        process = row[1]
        setup = row[2]
        tier = row[3]
        dbsInst = row[4]
        dbSizeGb = float(row[5])
        dbNFiles = int(row[6])
    # check whether information correct and adjust if needed
    changed = ((dbSizeGb-sizeGb)>0.0001 or dbNFiles != nFiles)
    if changed:
        print " Update!  Size: %.3f -> %.3f  nFiles: %d -> %d"%(dbSizeGb,sizeGb,dbNFiles,nFiles)
        print " Update!  Size: %f -> %f  nFiles: %d -> %d"%(dbSizeGb,sizeGb,dbNFiles,nFiles)
        rc = 0
        if exe:
            rc = updateDataset(db,process,setup,tier,sizeGb,nFiles,lfns,changed,debug)
        else:
            print ' not updating dataset: use --exec option'

        if rc == 0:
            print ' Updated dataset successfully in Bambu database (%s).'%(dataset)
        else:
            print ' Error updating dataset in Bambu database (%s).'%(dataset)
    else:
        print " Database is up to date.\n"
    sys.exit(0)

elif len(results) > 1:
    print ' Dataset exists already multiple times in database. ERROR please fix.'
    sys.exit(0)

rc = 0 
if exe:
    rc = insertDataset(db,process,setup,tier,dbsInst,sizeGb,nFiles,lfns,debug)
else:
    print ' not inserting dataset: use --exec option'

if rc == 0:
    print ' New dataset successfully inserted into the database (%s).'%(dataset)
else:
    print ' Error inserting dataset (%s).'%(dataset)

# disconnect from server
db.close()
