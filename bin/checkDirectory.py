#!/usr/bin/env python
#===================================================================================================
# This script checks all files in a given directory using the checkFile.py script and compares them
# to the files entered into the database. Any inconsitencies will be resolved.
#===================================================================================================
import os,sys,subprocess
import MySQLdb
import rex

usage = "   usage:  checkDirectory.py  <directory> \n"

Db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
Cursor = Db.cursor()

#===================================================================================================
#  H E L P E R S
#===================================================================================================
def getRequestId(directory):
    # extract the unique request id this file is part of

    requestId = -1
    datasetId = -1

    f = directory.split('/')

    # make sure we have a good file name
    if len(f) < 5:
        return (requestId, datasetId)
      
    # find parameters
    dataset = f[-1]
    version = f[-2]
    mitcfg = f[-3]

    # decode the dataset
    f = dataset.split('+')
    if len(f) < 3:
        print " ERROR - dataset name not correctly formed: " + dataset
        sys.exit(0)
    process = f[0]
    setup = f[1]
    tier = f[2]

    sql = "select RequestId, Datasets.DatasetId from Requests inner join Datasets on " \
        + " Datasets.DatasetId = Requests.DatasetId where " \
        + " DatasetProcess = '%s' and DatasetSetup='%s' and DatasetTier='%s'"%(process,setup,tier) \
        + " and RequestConfig = '%s' and RequestVersion = '%s'"%(mitcfg,version)

    #print ' SQL - ' + sql

    try:
        # Execute the SQL command
        Cursor.execute(sql)
        results = Cursor.fetchall()
    except:
        print 'ERROR(%s) - could not find request id.'%(sql)

    # found the request Id
    for row in results:
        requestId = int(row[0])
        datasetId = int(row[1])

    return (requestId, datasetId)

def findAllFilesInDb(requestId):
    nEvents = {}

    sql = "select FileName, NEvents from Files " \
        + " where RequestId=%d"%(requestId)
    #print ' SQL: ' + sql
    try:
        # Execute the SQL command
        Cursor.execute(sql)
        results = Cursor.fetchall()
    except:
        print " ERROR -- execution failed: " + sql 


    # found the request Id
    for row in results:
        name = row[0]
        nEvts = int(row[1])

        nEvents[name] = nEvts
    
    return nEvents

def removeDbEntry(requestId,fileId):
    # remove an entry from the database which does not have the corresponding file on disk

    sql = "delete from Files " \
        + " where RequestId=%d and FileName='%s'"%(requestId,fileId)
    #print ' SQL: ' + sql
    try:
        # Execute the SQL command
        Cursor.execute(sql)
        results = Cursor.fetchall()
    except:
        print " ERROR -- execution failed: " + sql 

    return

#===================================================================================================
#  M A I N
#===================================================================================================
# make sure command line is complete
if len(sys.argv) < 2:
    print "\n ERROR -- " + usage
    sys.exit(1)

# command line variables
directory = sys.argv[1]
print "\n INFO - checkDirectory.py %s"%(directory)
cmd = "t2tools.py --action ls --source " +  directory + " | grep root"
# make sure we can work remotely/locally
remoteX = rex.Rex('none','none')
(rc,out,err) = remoteX.executeLocalAction(cmd)

content = out.split("\n")

# get Ids in the database
(requestId,datasetId) = getRequestId(directory)
nEvents = findAllFilesInDb(requestId)

# get disk resident Ids
path = directory
fileIds = []
for line in content:
    f = line.split(" ")
    if len(f) > 1:
        file = f[1]
        g = file.split('/')
        g = (g[-1].split('.'))[0]
        fileIds.append(g)

# summarize data collection
print '\n INFO - On disk      %d\n INFO - In database  %d\n'%(len(fileIds),len(nEvents))

# check all ids from database whether they are on disk
print '\n -- Check database files'
for fileId,nEvts in nEvents.iteritems():
    if fileId in fileIds:
        pass
    else:
        print " Found fileId in database not on disk yet (%s). REMOVING ENTRY"%(fileId)
        removeDbEntry(requestId,fileId)

# check all ids from disk whether they are in database
missingInDb = []
print '\n -- Check disk resident files'
for fileId in fileIds:
    if fileId in nEvents.keys():
        pass
    else:
        print " Found fileId on disk but not in database yet (%s at %s)."%(fileId,path)
        missingInDb.append(path+'/'+fileId+'.root')
print ''

# process missing files to be added to the database
for file in missingInDb:
    cmd = "checkFile.py %s"%(file)
    print " %s"%(cmd)
    os.system(cmd)

print ''

sys.exit(0)
