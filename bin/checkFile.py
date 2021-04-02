#!/usr/bin/env python
#===================================================================================================
# This script checks a given file (argument) which is assumed to be located on the remote Tier-2
# storage and checks whether it is readable and has the number of events that are expected as
# derived from the input source. Files that are not compliant are deleted.
#
# Assuming now the file is complete. If the file is still located in a temporary directory it will
# be moved into its final location. If there is already a complete file in that location the new
# file will be deleted.
#
# The script relies on the catalogFile.sh script to be in its path. This script is responsible to
# perfrom the various tests on the file.
#===================================================================================================
import os,sys,subprocess,time,json,requests
import MySQLdb
import rex

Prefix = os.getenv('KRAKEN_TMP_PREFIX')
Db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
Cursor = Db.cursor()

DYNAMO_HOST = 't3serv009.mit.edu'
CERT = '/tmp/x509up_u%d' % os.getuid()

usage = "\n   usage:  checkFile.py  <file> \n"

#===================================================================================================
#  H E L P E R S
#===================================================================================================
def catalogFile(file):
    # perfrom cataloging operation on one file (return the entry)

    cmd = 'catalogFile.sh ' + file
    list = cmd.split(" ")
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode

    entry = ''
    lines = out.split("\n")
    for line in lines:
        if 'XX-CATALOG-XX 0000' in line:
            entry = line.replace('XX-CATALOG-XX 0000 ','')

    print '\n o-o-o OUT o-o-o \n%s\n\n o-o-o ERR (%d) o-o-o \n%s'%(out,rc,err)

    return (out,err,entry)

def findFileSize(file):

    size = 0
    cmd = "t2tools.py --action ls --source " +  file
    print ' LIST: ' + cmd
    (rc,out,err) = remoteX.executeLocalAction(cmd)
    size = long((out.split(" ")[0]).split(":")[1])
    print ' SIZE: %ld'%size 

    return size

def getName(file):
    # extract the unique file name

    f = file.split('/')
    fileName = (f.pop()).replace('.root','')
    fileName = fileName.replace('_tmp','')         # maybe this is a temporary file

    return fileName

def getFinalFile(file):
    # extract the unique file name

    finalFile = file

    if Prefix in file:
        f = file.split('/')
        tmp = f[-1].replace('_tmp','') 
        finalFile = "/".join(f[:-2])
        finalFile = finalFile + '/' + tmp
        
    return finalFile

def getFileInfo(file):
    # extract the unique request id this file is part of

    requestId = -1
    datasetId = -1
    nEventsLfn = -1
    blockName = ""

    f = file.split('/')

    # make sure we have a good file name
    if len(f) < 6:
        return (requestId, datasetId)
        

    if Prefix in file:
        dataset = f[-3]
        version = f[-4]
        mitcfg = f[-5]
    else:
        dataset = f[-2]
        version = f[-3]
        mitcfg = f[-4]

    # decode the dataset
    f = dataset.split('+')
    if len(f) < 3:
        print " ERROR - dataset name not correctly formed: " + dataset
        sys.exit(0)
    process = f[0]
    setup = f[1]
    tier = f[2]

    sql = "select RequestId, Datasets.DatasetId, BlockName, Lfns.NEvents from Requests" \
        + " inner join Datasets on Datasets.DatasetId = Requests.DatasetId" \
        + " inner join Blocks on Blocks.DatasetId = Datasets.DataSetId" \
        + " inner join Lfns on Lfns.BlockId = Blocks.BlockId" \
        + " where " \
        + " DatasetProcess = '%s' and DatasetSetup='%s' and DatasetTier='%s'"%(process,setup,tier) \
        + " and RequestConfig = '%s' and RequestVersion = '%s'"%(mitcfg,version) \
        + " and Lfns.FileName = '%s' "%(getName(file))

    print ' SQL - ' + sql

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
        blockName = row[2]
        nEventsLfn = int(row[3])

    return (requestId, datasetId, blockName, nEventsLfn, mitcfg, version, dataset)

def numberOfEventsInEntry(entry):
    # extract the number of events in a given catalog entry

    f = entry.split(" ")
    nEvents = -1
    if len(f)>2: 
        nEvents = int(f[2])

    return nEvents

def makeDatabaseEntry(requestId,fileName,nEvents,size):

    sql = "insert into Files(RequestId,FileName,NEvents,SizeBytes) " \
        + " values(%d,'%s',%d,%ld)"%(requestId,fileName,nEvents,size)
    print ' SQL: ' + sql
    try:
        # Execute the SQL command
        Cursor.execute(sql)
    except MySQLdb.IntegrityError as e:
        if not e[0] == 1062:
            print 'ERROR(%s) - could not insert new file.'%(sql)
            raise
        else:
            print " WARNING -- entry was already in table." 


#===================================================================================================
#  M A I N
#===================================================================================================
# make sure command line is complete
if len(sys.argv) < 1:
    print " ERROR -- " + usage
    sys.exit(1)

# command line variables
file = sys.argv[1]
print " INFO - checkFile.py %s"%(file)     
            
# doing the cataloging here: result is the number of events found in the file
(out,err,entry) = catalogFile(file)
nEvents = numberOfEventsInEntry(entry)

# check whether to delete in case of mismatch or zombie state
delete = os.environ.get('DELETE',False)
if "Object is in 'zombie' state" in out:
    delete = True
    print '\n o=o=o=o File corrupt, schedule deletion. o=o=o=o \n'

print ' CATALOG: %d -- %s'%(nEvents,file)

# find all relevant infromation about the file
fileName = getName(file)
(requestId,datasetId,blockName,nEventsLfn,config,version,dataset) = getFileInfo(file)

print ' Compare: %d [lfn] and %d [output]'%(nEventsLfn,nEvents)

# make sure we can work remotely
remoteX = rex.Rex('none','none')

if nEvents == nEventsLfn and nEvents>0:
    # now move file to final location
    finalFile = getFinalFile(file)
    size = findFileSize(file)
    if Prefix in file:
        cmd = "t2tools.py --action mv --source " +  file + " --target " + finalFile
        print ' MOVE: ' + cmd
        (rc,out,err) = remoteX.executeLocalAction(cmd)
        if rc != 0:
            print ' ERROR -- move failed: %d\n  - out:\n %s\n  - err:\n %s'%(rc,out,err)
            if ': File exists' in out:
                print ' REASON -- file exists: %s'%(finalFile)
                cmd = "t2tools.py --action rm --source " +  file
                print ' REMOVE: ' + cmd
                (rc,out,err) = remoteX.executeLocalAction(cmd)
                
    
    # add a new catalog entry
    makeDatabaseEntry(requestId,fileName,nEvents,size)
    ## add the file to dynamo
    #os.system("dynamo-inject-one-file %s"%(finalFile))

else:
    print ' ERROR: event counts disagree or not positive (LFN %d,File %d). EXIT!'%\
        (nEventsLfn,nEvents)

    if delete:
        cmd = "t2tools.py --action rm --source " +  file
        print ' REMOVE: ' + cmd
        (rc,out,err) = remoteX.executeLocalAction(cmd)
