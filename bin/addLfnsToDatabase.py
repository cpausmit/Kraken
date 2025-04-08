#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Add all lfns of a given dataset to the database.
#
# v1.0                                                                                  Oct 14, 2016
#---------------------------------------------------------------------------------------------------

import sys,os,subprocess,getopt,time
import MySQLdb

TRUNC = "/cms"
DIR = "/store/user/paus"
LFNROOT = "/home/cmsprod/cms/jobs/lfns"

#===================================================================================================
#  H E L P E R S
#===================================================================================================
def addAllLfnsForDataset(dataset):

    # First get the dataset id
    datasetId = getDatasetId(dataset)
    
    # Load table of all existing lfns
    lfns = loadExistingLfns(datasetId)
    
    # Read the lfn file
    blockId = -1
    lastBlockName = "EMPTY"
    with open(LFNROOT + '/' + dataset + '.lfns','r') as fHandle:
        for line in fHandle:
            f = line[:-1].split(" ")
            if len(f) != 3:
                print ' ERROR invalid line: ' + line
            else:
                # Decode the relevant information
                blockName = (f[0].split("#"))[1]
                file = f[1]
                fileName = (file.split('/')).pop()
                fileName = fileName.replace('.root','')
                pathName = '/'.join((file.split('/'))[:-1])
                nEvents = int(f[2])
    
                # check whether already in database and skip if already there
                if fileName in lfns:
                    #print ' Already have: %s moving on.'%(fileName)
                    continue
    
                if blockName != lastBlockName:
                    blockId = addBlock(datasetId,blockName)
    
                if isValidId(blockId):
                    addLfn(datasetId,blockId,fileName,pathName,nEvents)
    
                lastBlockName = blockName

    return

def addBlock(datasetId,blockName):
    # add a new block of a given datasetId to the database

    sql  = "insert into Blocks(DatasetId,BlockName) values(%d,'%s')"%(datasetId,blockName)
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print ' ERROR (%s) - could not insert new block.'%(sql)
        print " Unexpected error:", sys.exc_info()[0]

    return getBlockId(datasetId,blockName)

def addLfn(datasetId,blockId,fileName,pathName,nEvents):
    # add an lfn to a given datasetId of a given blockId

    sql = "insert into Lfns(DatasetId,BlockId,FileName,PathName,NEvents) " \
        +  " values(%d,%d,'%s','%s',%d)"%(datasetId,blockId,fileName,pathName,nEvents)
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print ' ERROR (%s) - could not insert new file.'%(sql)
        print " Unexpected error:", sys.exc_info()[0]

    return

def findAllDatasets(book,pattern):
    # find all datasets on Tier-2 in a given book matching a given pattern
   
    allDatasets = []

    if pattern == '':
        print ' Find all datasets.'
    else:
        print ' Find all datasets matching pattern: %s.'%(pattern)
    
    cmd = 'list ' + TRUNC + DIR + "/" + book
    if pattern != "":
        cmd += "| grep %s"%(pattern)
    
    for line in os.popen(cmd).readlines():
        f = (line[:-1].split("/"))[-1:]
        dataset = "/".join(f)
        allDatasets.append(dataset)
    print ' Number of datasets found: %d'%(len(allDatasets))

    return allDatasets
    
def getBlockId(datasetId,blockName):
    # find the blockId for a given data block

    blockId = -1

    sql = "select BlockId from Blocks where " \
        + "DatasetId=%d and BlockName='%s';"%(datasetId,blockName)
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " ERROR (%s): unable to fetch data."%(sql)
        sys.exit(0)

    blockId = int(results[0][0])
    if not isValidId(blockId):
        print ' ERROR -- invalid block id: %d'%(blockId)
        sys.exit(1)
 
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
 
    if not isValidId(datasetId):
        print ' ERROR -- invalid dataset id: %d'%(datasetId)
        sys.exit(1)
            
    return datasetId

def isValidId(id):
    # make sure the Id is larger zero

    valid = True
    if id<=0:
        valid = False

    return valid

def loadExistingLfns(datasetId):
    # load all lfns for an existing dataset

    localLfns = []

    sql = "select FileName from Lfns where DatasetId=%d"%(datasetId)
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " ERROR (%s): unable to fetch data."%(sql)
        sys.exit(1)

    for row in results:
        lfnName = row[0]
        localLfns.append(lfnName)

    return localLfns

def testLocalSetup(book):
    # test all relevant components and exit is something is off

    # check the input parameters
    if book == '':
        print ' Error - no book specified. EXIT!\n'
        print usage
        sys.exit(1)

    return

#===================================================================================================
#  M A I N
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: addLfnsToDatabase.py  --book=<book> --pattern=<name>\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','pattern=',"help"]
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
book = ''
pattern = ''

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--book":
        book = arg
    if opt == "--pattern":
        pattern = arg

# Make sure our local setup is good
testLocalSetup(book)

# Make a list of all directories
allDatasets = findAllDatasets(book,pattern)

# Open database connection
db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
cursor = db.cursor()

# Loop over all matched datasets
for dataset in allDatasets:
    print ' Process Dataset: ' + dataset
    addAllLfnsForDataset(dataset)

# disconnect from server
db.close()
