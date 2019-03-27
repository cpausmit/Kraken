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

    # count number of files per dataset
    nfiles_all = {} # all files in dataset replica
    nfiles = {}     # files available in block replica of the dataset replica

    # loop through all datasets
    for dataset in inventory.datasets.itervalues():

        # only one specific book
        if dataset.name.startswith('%s/%s'%(config,version)):

            nfiles_all[dataset.name] = len(dataset.files)

            # only consider one site?
            if site != 0:
                for dr in dataset.replicas:
                    if site == dr.site.name:
                        # any dataset replica at a given site counts
                        nfiles[dr.dataset.name] = 0
                        for br in dr.block_replicas:
                            if site == br.site.name:
                                #print ' Available: d(%s), b(%s)'%(dr.dataset.name,br.block.name)
                                for dlfn in br.files():
                                    name = "/".join((dlfn.lfn).split("/")[-2:])
                                    dlfns[name] = dlfn.size

                                    if dr.dataset.name in nfiles:
                                        nfiles[dr.dataset.name] += 1
                                    else:
                                        nfiles[dr.dataset.name] = 1

                            else:
                                #print ' Available as dr(%s) but not as br(%s)'%(dr.dataset.name,br.block.name)
                                for dlfn in br.files():
                                    name = "/".join((dlfn.lfn).split("/")[-2:])
                                    dlfns[name] = dlfn.size
                                
                        break
                    
            else:
                for dlfn in dataset.files:
                    name = "/".join((dlfn.lfn).split("/")[-2:])
                    dlfns[name] = dlfn.size


    return (dlfns,nfiles_all,nfiles)

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: makeListOfFilesFromInventory.py"
usage += "  [ --book=pandaf/004 [ --site=T3_US_MIT [ --help ] ] ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','site=','verbose','help']
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
verbose = 0
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
    if opt == "--verbose":
        verbose = 1

config = book.split("/")[0]
version = book.split("/")[1]

(dlfns,nfiles_all,nfiles) = findAllDynamoFiles(config,version,site)

# print some summary statement
if verbose > 0:
    n_total = 0
    n_missing = 0
    for dset,n in nfiles.items():
        print " %5d/%5d -- %s"%(n,nfiles_all[dset],dset)
        n_total += nfiles_all[dset]
        n_missing += nfiles_all[dset]-n
    
    print " ============================"
    print " %5d/%5d -- total missing"%(n_missing,n_total)

# generate a clean slate
of = "/tmp/.inventory_%s_%s_%s.tmp"%(site,config,version)
os.system("rm %s"%(of))
os.system("touch %s"%(of))

# write your output
with open(of,"w") as fH:
    for dlfn in sorted(dlfns):
        fH.write("%d /cms/store/user/paus/%s/%s\n"%(dlfns[dlfn],book,dlfn))
