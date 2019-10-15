#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Script to review all samples which are kept in our database and take approriate action to get
# them into the processing queues.
#
# Author: C.Paus                                                                (September 23, 2008)
#---------------------------------------------------------------------------------------------------
import os,sys,getopt,re,string
import MySQLdb
import rex

from cleaner import Cleaner
from request import Request
from sample import Sample
from scheduler import Scheduler
from task import Task

PREFIX = os.getenv('KRAKEN_TMP_PREFIX')
CATALOG = os.getenv('KRAKEN_CATALOG_OUTPUT')
JOBS = os.getenv('KRAKEN_WORK') + '/jobs'

#---------------------------------------------------------------------------------------------------
# H E L P E R
#---------------------------------------------------------------------------------------------------
def cleanupTask(task):
    # cleanup task at hand

    # ----------------------------------------------------------------------------------------------
    # Get all parameters for the production
    # ----------------------------------------------------------------------------------------------
    cleaner = Cleaner(task)
    cleaner.logCleanup()

    print ''

    return

def displayLine(row):

    process = row[0]
    setup = row[1]
    tier = row[2]
    dbs = row[3]
    nFiles = int(row[4])
    requestId = int(row[8])
    dbNFilesDone = int(row[9])

    # make up the proper mit dataset name
    datasetName = process + '+' + setup+ '+' + tier
    (nDone,nAll) = productionStatus(config,version,datasetName,debug)

    percentage = 0.0
    if nAll > 0:
        percentage = 100.0 * float(nDone)/float(nAll)

    if nDone != nAll:
        print "  %6.2f  %5d/ %5d  %s"%(percentage,nDone,nAll,datasetName)
    else:
        print "  %6.2f  %5d= %5d  %s"%(percentage,nDone,nAll,datasetName)


def findDomain():
    domain = os.uname()[1]
    f = domain.split('.')

    return '.'.join(f[1:])

def findNumberOfFilesDone(config,version,dataset,debug=0):
    # Find out how many files have been completed for this dataset so far

    if debug > 0:
        print " Find completed files for dataset: %s"%(dataset)

    cmd = "list /cms/store/user/paus/%s/%s/%s 2> /dev/null | grep .root | wc -l"\
        %(config,version,dataset)
    if debug > 0:
        print " CMD: %s"%(cmd)

    nFilesDone = 0
    try:
        for line in os.popen(cmd).readlines():   # run command
            nFilesDone = int(line[:-1])
    except:
        nFileDone = -1

    return nFilesDone

def findPath(config,version):
    # Find the path to where we store our samples

    # start with T2_US_MIT as default
    storageTag = 'T2_US_MIT'
    domain = findDomain()
    if   re.search('mit.edu',domain):
        storageTag = 'T2_US_MIT'
    elif re.search('cern.ch',domain):
        storageTag = 'T0_CH_CERN'
    # make connection with our storage information
    seTable = os.environ['KRAKEN_BASE'] + '/' + config + '/' + version + '/' + 'seTable'
    if not os.path.exists(seTable):
        cmd = "seTable file not found: %s" % seTable
        raise RuntimeError, cmd
    # extract the path name
    cmd = 'grep ^' + storageTag + ' ' + seTable + ' | cut -d = -f2 | sed \'s# : ##\''
    path = ''
    for line in os.popen(cmd).readlines():
        path = line[:-1] +  '/' + config + '/' + version

    return path

def generateCondorId():
    # condor id
    cmd = "date +" + PREFIX + "%y%m%d_%H%M%S"
    for line in os.popen(cmd).readlines():  # run command
        line = line[:-1]
        condorId = line
        
    print "\n CondorId: " + condorId + "\n"

    return condorId

def productionStatus(config,version,dataset,debug=0):
    # make sure we can see the Tier-2 disks: returns -1 on failure

    cmd = "cat %s/%s/%s/%s/Files 2> /dev/null | wc -l"\
        %(CATALOG,config,version,dataset)
    if debug > 0:
        print " CMD: %s"%(cmd)

    nDone = 0
    try:
        for line in os.popen(cmd).readlines():   # run command
            nDone = int(line[:-1])
    except:
        nDone = -1

    cmd = "grep root %s/%s.jobs 2> /dev/null | wc -l"%(JOBS,dataset)
    if debug > 0:
        print " CMD: %s"%(cmd)

    nAll = 0
    try:
        for line in os.popen(cmd).readlines():   # run command
            nAll = int(line[:-1])
    except:
        nAll = -1
    
    return(nDone,nAll)

def setupScheduler(local,nJobsMax):
    # Setup the scheduler we are going to use (once for all following submissions)

    scheduler = None
    if local:
        scheduler = Scheduler('t3serv015.mit.edu',os.getenv('USER','paus'),nJobsMax)
    else:
        scheduler = Scheduler('submit.mit.edu',
                              os.getenv('KRAKEN_REMOTE_USER','paus'),
                              '/work/%s'%(os.getenv('KRAKEN_REMOTE_USER','paus')),
                              nJobsMax)
    return scheduler

def submitTask(task):
    # Submit the task at hand

    # ----------------------------------------------------------------------------------------------
    # Get all parameters for the production
    # ----------------------------------------------------------------------------------------------

    # Prepare the environment
    if len(task.sample.missingJobs) > 0:
    
        # Make the local/remote directories
        if not task.createDirectories():
            return

        # Prepare the tar ball if needed
        task.makeTarBall()
    
        # Make the submit file
        task.writeCondorSubmit()
     
        # Submit this job
        task.condorSubmit()
    
        # Make it clean
        task.cleanUp()

    else:
        # Nothing to do here
        print '\n INFO - we are done here.\n'
        
    return

def testEnvironment(config,version,py):
    # Basic checks will be implemented here to remove the clutter from the main

    # Does the local environment exist?
    dir = './' + config + '/' + version
    if not os.path.exists(dir):
        os.system('hostname')
        os.system('pwd')
        cmd = "\n Local work directory does not exist: %s\n" % dir
        raise RuntimeError, cmd
 
    # Look for the standard CMSSW python configuration file (empty file is fine)
    cmsswFile = os.environ['KRAKEN_BASE'] + '/' + config + '/' + version + '/' + py + '.py'
    if not os.path.exists(cmsswFile):
        cmd = "Cmssw file not found: %s" % cmsswFile
        raise RuntimeError, cmd

    # Make sure the Tier-2 is up and running
    testResult = testTier2Disk(debug)
    if debug>0:
        print ' Test result: %d'%(testResult) 
    
    if testResult != 0:
        print '\n ERROR -- Tier-2 disks seem unavailable, please check! EXIT review process.\n'
        sys.exit(0)
    else:
        print '\n INFO -- Tier-2 disks are available, start review process.\n'

def testTier2Disk(debug=0):
    # make sure we can see the Tier-2 disks: returns -1 on failure

    cmd = "list /cms/store/user/paus 2> /dev/null"
    if debug > 0:
        print " CMD: %s"%(cmd)

    myRx = rex.Rex()
    (rc,out,err) = myRx.executeLocalAction("list /cms/store/user/paus 2> /dev/null")

    if debug > 0:
        print " RC: %d\n OUT:\n%s\n ERR:\n%s\n"%(rc,out,err)

    return rc

#---------------------------------------------------------------------------------------------------
# M A I N
#---------------------------------------------------------------------------------------------------
# Define string to explain usage of the script
usage  = "\nUsage: reviewRequests.py --config=<name>\n"
usage += "                         --version=<version> [ default: MIT_VERS ]\n"
usage += "                         --py=<name>\n"
usage += "                         --pattern=<name>\n"
usage += "                         --nJobsMax=<n>\n"
usage += "                         --useExistingLfns\n"
usage += "                         --useExistingJobs\n"
usage += "                         --useExistingSites\n"
usage += "                         --displayOnly=<status> [ default: 0, 1-all, 2-incomplete only ]\n"
usage += "                         --local\n"
usage += "                         --submit\n"
usage += "                         --cleanup\n"
usage += "                         --debug\n"
usage += "                         --help\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['config=','version=','py=','pattern=','nJobsMax=','displayOnly=', \
         'help','cleanup','submit','useExistingLfns','useExistingJobs','useExistingSites','local',
         'debug']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# Get all parameters for the production
# -------------------------------------
# Set defaults for each option
config = 'filefi'
version = '000'
py = 'data'
pattern = ''
nJobsMax = 40000
displayOnly = 0
cleanup = False
submit = False
useExistingLfns = False
useExistingJobs = False
useExistingSites = False
local = False
debug = False

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--config":
        config = arg
    if opt == "--version":
        version = arg
    if opt == "--py":
        py = arg
    if opt == "--pattern":
        pattern = arg
    if opt == "--nJobsMax":
        nJobsMax = int(arg)
    if opt == "--displayOnly":
        displayOnly = int(arg)
    if opt == "--cleanup":
        cleanup = True
    if opt == "--submit":
        submit = True
    if opt == "--useExistingLfns":
        useExistingLfns = True
    if opt == "--useExistingJobs":
        useExistingJobs = True
    if opt == "--useExistingSites":
        useExistingSites = True
    if opt == "--debug":
        debug = True

# Access the database to determine all requests
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
cursor = db.cursor()
sql = 'select ' + \
    'Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,'+\
    'Datasets.DatasetDbsInstance,Datasets.DatasetNFiles,' + \
    'RequestConfig,RequestVersion,RequestPy,RequestId,RequestNFilesDone from Requests ' + \
    'left join Datasets on Requests.DatasetId = Datasets.DatasetId '+ \
    'where RequestConfig="' + config + '" and RequestVersion = "' + version + \
    '" and RequestPy = "' + py + \
    '" order by Datasets.DatasetProcess, Datasets.DatasetSetup, Datasets.DatasetTier;'
if debug:
    print ' SQL: ' + sql

# Try to access the database
try:
    # Execute the SQL command
    cursor.execute(sql)
    results = cursor.fetchall()      
except:
    print " Error (%s): unable to fetch data."%(sql)
    sys.exit(0)

#==========================================
# F I L T E R  A N D  S E L E C T  L O O P
#==========================================

# Take the result from the database and look at it
filteredResults = []
incompleteResults = []
nDone = 0
nAll = 0
nAllTotal = 0
nDoneTotal = 0
nMissingTotal = 0

# initial filter and calculation loop
for row in results:
    
    if debug:
        print row

    if row[0] is None:
        print " Row[0] is null"
        print row
        continue

    process = row[0]
    setup = row[1]
    tier = row[2]
    dbs = row[3]
    nFiles = int(row[4])
    requestId = int(row[8])
    dbNFilesDone = int(row[9])

    # make up the proper mit dataset name
    datasetName = process + '+' + setup+ '+' + tier

    if pattern in datasetName:
        (nDone,nAll) = productionStatus(config,version,datasetName,debug)
        nMissing = nAll-nDone

        # filtered list
        filteredResults.append(row)

        if nMissing > 0 or nAll == 0 or (nAll != 0 and nDone == 0):
            # incomplete and filtered result
            incompleteResults.append(row)

        nAllTotal += nAll
        nDoneTotal += nDone
        nMissingTotal += nMissing

# finish up the calculations
percentageTotal = 0.0
if nAllTotal > 0:
    percentageTotal = 100.0 * float(nDoneTotal)/float(nAllTotal)

#========================
# D I S P L A Y  L O O P
#========================

print '#---------------------------------------------------------------------------'
print '#'
print '#                            O V E R V I E W '
print '#                              %s/%s'%(config,version)
print '#'
print '# Perct    Done/ Total--Dataset Name'
print '# ----------------------------------'
print '# %6.2f  %5d/ %5d  TOTAL         -->  %6.2f%% (%d) missing.'\
    %(percentageTotal,nDoneTotal,nAllTotal,100.-percentageTotal,nMissingTotal)
print '#---------------------------------------------------------------------------'

# incomplete in alphabetic order
if displayOnly == 2:
    for row in incompleteResults:
        displayLine(row)

# all in alphabetic order
if displayOnly == 1:
    for row in filteredResults:
        displayLine(row)

print '#'
print '# %6.2f  %5d/ %5d  TOTAL         -->  %6.2f%% (%d) missing.'\
    %(percentageTotal,nDoneTotal,nAllTotal,100.-percentageTotal,nMissingTotal)
print '#'

if displayOnly != 0:
    sys.exit(0)

# Basic tests first
testEnvironment(config,version,py)

# Where is our storage?
path = findPath(config,version)

# Decide which list to work through
if cleanup:
    loopSamples = filteredResults
else:
    loopSamples = incompleteResults

#==================
# M A I N  L O O P
#==================

# Make sure we have a valid ticket, because now we will need it
cmd = "voms-proxy-init --valid 168:00 -voms cms | grep 'Your proxy'"
os.system(cmd)

# Get our scheduler ready to use
scheduler = setupScheduler(local,nJobsMax)

# Initial message 
print ''
print ' @-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@'
print ''
print '                    S T A R T I N G   R E V I E W   C Y L E '
print ''
print ' @-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@-@'

# Take the result from the database and look at it
for row in loopSamples:
    process = row[0]
    setup = row[1]
    tier = row[2]
    dbs = row[3]
    nFiles = int(row[4])
    requestId = int(row[8])
    dbNFilesDone = int(row[9])

    # make up the proper mit datset name
    datasetName = process + '+' + setup+ '+' + tier

    # check how many files are done
    nFilesDone = findNumberOfFilesDone(config,version,datasetName)
    print ' Number of files completed: %d (last check: %d) -- Dataset: %s' \
        %(nFilesDone,dbNFilesDone,datasetName)

    # what to do when the two numbers disagree
    if dbNFilesDone == -1:
        # this is a new dataset
        print '\n INFO - this seems to be a new dataset.'
        pass
        
    elif dbNFilesDone != nFilesDone:
        lUpdate = False

        # assume more files have been found
        if nFilesDone > 0 and nFilesDone > dbNFilesDone:
            lUpdate = True
        # less files are done now than before (this is a problem)
        else:
            if nFilesDone > 0: # looks like files have disappeared, but not all -> we should update
                lUpdate = True
                print '\n WARNING -- files have disappeared but there are files (%d -> %d now)'\
                    %(dbNFilesDone,nFilesDone)
            else:              # looks like we did not connect with the storage
                lUpdate = False
                print '\n WARNING -- files have all disappeared, very suspicious (%d -> %d now)'\
                    %(dbNFilesDone,nFilesDone)

        # 
        if lUpdate:
            sql = 'update Requests set RequestNFilesDone=%d'%(nFilesDone) + \
                ' where RequestId=%d'%(requestId)
            if debug:
                print ' SQL: ' + sql

            # Try to access the database
            try:
                # Execute the SQL command
                cursor.execute(sql)
                results = cursor.fetchall()      
            except:
                print " Error (%s): unable to update the database."%(sql)
                sys.exit(0)
        
    # did we already complete the job?
    if not cleanup:
        if nFilesDone == nFiles:   # this is the case when all is done
            print ' DONE all files have been produced.\n'
            continue
        elif nFilesDone < nFiles:  # second most frequent case: work started but not completed
            print ' files missing, submit the missing ones.\n'
        else:                      # weird, more files found than available               
            print '\n ERROR more files found than available in dataset. NO ACTION on this dataset'
            print '       done: %d   all: %d'%(nFilesDone,nFiles)
            cmd = 'addDataset.py --exec --dataset=' + datasetName
            print '       updating the dataset from dbs: ' + cmd
            os.system(cmd)
    
    # if work not complete consider further remainder
    print '\n # # # #  New dataset: %s  # # # # \n'%(datasetName)

    # Get sample info, make request and generate the task
    sample = Sample(datasetName,dbs,useExistingLfns,useExistingLfns,useExistingSites)
    request = Request(scheduler,sample,config,version,py)
    task = Task(generateCondorId(),request)

    # Submit task
    if submit:
        cleanupTask(task)
        submitTask(task)

    # Cleanup task (careful all tasks being submitted get cleaned up)
    if cleanup and row not in incompleteResults:
        cleanupTask(task)

sys.exit(0)
