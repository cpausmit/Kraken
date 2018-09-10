#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------
# Remove datasets that are already available in a newer version.
#
# v1.0                                                                                  May 24, 2017
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import rex

BASE = '/cms/store/user/paus'
COMPLETION_MIN = 0.90         # 90% completion required before deleting the old dataset

# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: removeObsoleteDatasets.py  --config=<name>\n"
usage += "                                   --oldVersion=<name>\n"
usage += "                                   --newVersion=<name>\n"
usage += "                                 [ --debug=0 ]\n"
usage += "                                 [ --exec (False) ]\n"
usage += "                                 [ --help ]\n\n"

def testLocalSetup(config,oldVersion,newVersion,debug):
    # test all relevant components and exit is something is off

    # check the input parameters
    if config == '':
        print ' Error - no config specified. EXIT!\n'
        print usage
        sys.exit(1)
    if oldVersion == '':
        print ' Error - no old version specified. EXIT!\n'
        print usage
        sys.exit(1)
    if newVersion == '':
        print ' Error - no new version specified. EXIT!\n'
        print usage
        sys.exit(1)

    if oldVersion == newVersion:
        print ' Error - WARNING - old and new version identical. EXIT!\n'
        print usage
        sys.exit(1)

def makeDatasetList(config,version):

    myRx = rex.Rex()
    (rc,out,err) = myRx.executeLocalAction("list %s/%s/%s 2> /dev/null | grep ^D:"
                                           %(BASE,config,version))
    datasetList = []
    for line in out.split("\n"):
        dataset = line.split("/")[-1]
        if len(dataset) > 4:
            datasetList.append(dataset)

    if debug > 0:
        print " RC: %d\n OUT:\n%s\n ERR:\n%s\n"%(rc,out,err)

    return datasetList

def numberOfFiles(config,version,dataset):

    nFiles = -1
    myRx = rex.Rex()
    (rc,out,err) = myRx.executeLocalAction("list %s/%s/%s/%s/*.root 2> /dev/null"
                                           %(BASE,config,version,dataset))
    nFiles = len(out.split("\n"))
    return nFiles

#===================================================================================================
# Main starts here
#===================================================================================================

# Define the valid options which can be specified and check out the command line
valid = ['config=','oldVersion=','newVersion=','debug=','exec','help']
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
dataset = ''
config = ''
oldVersion = ''
newVersion = ''

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--config":
        config = arg
    if opt == "--oldVersion":
        oldVersion = arg
    if opt == "--newVersion":
        newVersion = arg
    if opt == "--exec":
        exe = True
    if opt == "--debug":
        debug = int(arg)

# make sure the request makes sense
testLocalSetup(config,oldVersion,newVersion,debug)

# make list of datasets with old version
oldDatasetsList = makeDatasetList(config,oldVersion)
newDatasetsList = makeDatasetList(config,newVersion)

# find obsolete datasets
i = 0
for dataset in oldDatasetsList:
    if dataset in newDatasetsList:

        nFilesOld = numberOfFiles(config,oldVersion,dataset)
        nFilesNew = numberOfFiles(config,newVersion,dataset)

        py = 'data'
        if 'AODSIM' in dataset:
            py = 'mc'

        if nFilesNew > COMPLETION_MIN * nFilesOld:
            print ' Deleting obsolete data: (%3d) %s -- %s (%d/%d)' \
                %(i,oldVersion,dataset,nFilesNew,nFilesOld)
            cmd = 'removeData.py --exec --config=%s --version=%s --py=%s --pattern=%s' \
                %(config,oldVersion,py,dataset)
            print ' rmr: ' + cmd
            if exe:
                os.system(cmd)
            i += 1
        else:
            print ' Not complete enough   : (---) %s -- %s (new/old: %d/%d)' \
                %(oldVersion,dataset,nFilesNew,nFilesOld)
    else:
        if debug > 0:
            print ' Keeping this dataset  : (---) %s -- %s'%(oldVersion,dataset)
