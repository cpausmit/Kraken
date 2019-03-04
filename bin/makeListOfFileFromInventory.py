#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Simply make a list of files from the dynamo inventory, for later usage.
# v1.0                                                                                  Jul 16, 2018
#---------------------------------------------------------------------------------------------------
import os
import sys
import getopt
from dynamo.core.executable import inventory

def findAllDynamoFiles(config,version,site=0):

    # find all files injected into dynamo
    dlfns = {}
    for dataset in inventory.datasets.itervalues():
        files = []
        if dataset.name.startswith('%s/%s'%(config,version)):
            # only consider one site?
            selected = True
            if site != 0:
                selected = False
                for replica in dataset.replicas:
                    if site == replica.site.name:
                        #print ' Matched: ' + site + ' ' + replica.site.name
                        selected = True
                        for br in replica.block_replicas:
                            for f in br.files():
                                files.append(f)
                        break
            if selected:
                for dlfn in dataset.files:
                    name = "/".join((dlfn.lfn).split("/")[-2:])
                    dlfns[name] = dlfn.size

    return dlfns

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: makeListOfFilesFromInventory.py"
usage += "  [ --book=pandaf/004 [ --site=T3_US_MIT [ --help ] ] ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','site=','help']
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
book = "pandaf/012"
site = 0

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--book":
        book = arg
    if opt == "--site":
        site = arg

config = book.split("/")[0]
version = book.split("/")[1]

dlfns = findAllDynamoFiles(config,version,site)

with open("/tmp/.inventory_%s_%s_%s.tmp"%(site,config,version),"w") as fH:
    for dlfn in sorted(dlfns):
        fH.write("%d /cms/store/user/paus/%s/%s\n"%(dlfns[dlfn],book,dlfn))
