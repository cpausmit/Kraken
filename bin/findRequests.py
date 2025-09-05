#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Script to collect all requests from the DB.
#
# Author: C.Paus                                                                (September 05, 2025)
#---------------------------------------------------------------------------------------------------
import os,sys,getopt,re,string
import MySQLdb
import rex

def getAllRequests(config,version,py):
    # collect all datasets matching this set of (config,version,py), no further selection yet
    
    results = []

    # Access the database to determine all requests
    db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
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
        print(' SQL: ' + sql)
    
    # Try to access the database
    try:
        # Execute the SQL command
        cursor.execute(sql)
        requests = cursor.fetchall()      
    except:
        print(" Error (%s): unable to fetch data."%(sql))
        sys.exit(0)
        
    return requests

def testEnvironment(config,version,py):
    # Basic checks will be implemented here to remove the clutter from the main

    # Does the local environment exist?
    dir = './' + config + '/' + version
    if not os.path.exists(dir):
        os.system('hostname')
        os.system('pwd')
        cmd = "\n Local work directory does not exist: %s\n" % dir
        raise RuntimeError(cmd)
 
    # Look for the standard CMSSW python configuration file (empty file is fine)
    cmsswFile = os.environ['KRAKEN_BASE'] + '/' + config + '/' + version + '/' + py + '.py'
    if not os.path.exists(cmsswFile):
        cmd = "Cmssw file not found: %s" % cmsswFile
        raise RuntimeError(cmd)

    # Make sure the Tier-2 is up and running
    testResult = testTier2Disk(debug)
    if debug>0:
        print(' Test result: %d'%(testResult))
    
    if testResult != 0:
        print('\n ERROR -- Tier-2 disks seem unavailable, please check! EXIT review process.\n')
        sys.exit(0)
    else:
        print('\n INFO -- Tier-2 disks are available, start review process.\n')

    # Make sure we have a valid ticket, because now we will need it
    cmd = "voms-proxy-init --valid 168:00 -voms cms >& /dev/null; scp -q `voms-proxy-info -p` paus@localhost:tmp/"
    os.system(cmd)
    os.system("voms-proxy-info -timeleft| awk '{print \" certificate valid for \" $1/3600 \" hrs\"}'")
    print(f" copied to submit at: paus@localhost:tmp/")
    
    return
    
def testTier2Disk(debug=0):
    # make sure we can see the Tier-2 disks: returns -1 on failure

    rc_total = 0

    cmd = "list /cms/store/user/paus 2> /dev/null"
    if debug > 0:
        print(" CMD: %s"%(cmd))
    myRx = rex.Rex()
    (rc,out,err) = myRx.executeLocalAction("list /cms/store/user/paus 2> /dev/null")
    if debug > 0:
        print(" RC: %d\n OUT:\n%s\n ERR:\n%s\n"%(rc,out,err))
    rc_total += rc

        
    cmd = "echo 'testing writing to Tier-2' > test.bak; remove /cms/store/user/paus/test.bak 2> /dev/null; upload test.bak /cms/store/user/paus/test.bak"
    if debug > 0:
        print(" CMD: %s"%(cmd))
    myRx = rex.Rex()
    (rc,out,err) = myRx.executeLocalAction("list /cms/store/user/paus 2> /dev/null")
    if debug > 0:
        print(" RC: %d\n OUT:\n%s\n ERR:\n%s\n"%(rc,out,err))
    rc_total += rc

    return rc_total

#---------------------------------------------------------------------------------------------------
# M A I N
#---------------------------------------------------------------------------------------------------
# Define string to explain usage of the script
usage  = "\nUsage: reviewRequests.py --config=<name>\n"
usage += "                         --version=<version> [ default: MIT_VERS ]\n"
usage += "                         --py=<name>\n"
usage += "                         --pattern=<name>\n"
usage += "                         --debug\n"
usage += "                         --help\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['config=','version=','py=','pattern=','help','debug']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# Get all parameters for the production
# -------------------------------------
# Set defaults for each option
config = 'filefi'
version = '000'
py = 'data'
pattern = ''
debug = False

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--config":
        config = arg
    if opt == "--version":
        version = arg
    if opt == "--py":
        py = arg
    if opt == "--pattern":
        pattern = arg
    if opt == "--debug":
        debug = True

testEnvironment(config,version,py)
allRequests = getAllRequests(config,version,py)

for request in allRequests:
    d = f"{request[0]}+{request[1]}+{request[2]}"
    if pattern in d:
        print(request)

sys.exit(0)
