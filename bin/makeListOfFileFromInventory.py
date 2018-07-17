#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Simply make a list of files from the dynamo inventory, for later usage.
# v1.0                                                                                  Jul 16, 2018
#---------------------------------------------------------------------------------------------------
import os
import sys
import getopt
from dynamo.core.executable import inventory

def findAllDynamoFiles(config,version):

    # find all files injected into dynamo
    dlfns = set()
    for dataset in inventory.datasets.itervalues():
        if dataset.name.startswith('%s/%s'%(config,version)):
            for dlfn in dataset.files:
                dlfn = "/".join((dlfn.lfn).split("/")[-2:])
                dlfns.add(dlfn)

    return dlfns

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: makeListOfFilesFromInventory.py  [ --book=pandaf/004 [ --help ] ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','help']
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
book = "pandaf/004"

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--book":
        book = arg

config = book.split("/")[0]
version = book.split("/")[1]

dlfns = findAllDynamoFiles(config,version)

with open("/tmp/.inventory_%s_%s.tmp"%(config,version),"w") as fH:
    for dlfn in dlfns:
        fH.write("/cms/store/user/paus/%s/%s\n"%(book,dlfn))
