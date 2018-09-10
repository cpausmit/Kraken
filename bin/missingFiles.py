#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Find missing data and orphan data on disk.
#
# v1.0                                                                                  Jul 20, 2018
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import MySQLdb
import rex

def findAllFiles(book,dataset):

    print " INFO - loading all physical files (Tier-2)."

    cmd = "gfal-ls gsiftp://se01.cmsaf.mit.edu:2811/cms/store/user/paus/%s/%s "%(book,dataset) \
        + "|grep root"
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    # find list
    files = set()
    for row in out.split("\n"):
        if len(row) < 2:
            continue
        filename = "%s/%s"%(dataset,row)
        files.add(filename)

    return files

def findLocalFiles(book,dataset):

    print " INFO - loading local physical files (Tier-3)."

    cmd = "hdfs dfs -ls /cms/store/user/paus/%s/%s "%(book,dataset) + "|grep root"
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    lines = out.split("\n")
    # in case hdfs is not installed
    if len(lines)<2:
        cmd = "ls -1 /mnt/hadoop/cms/store/user/paus/%s/%s "%(book,dataset) + "|grep root"
        myRx = rex.Rex()  
        (rc,out,err) = myRx.executeLocalAction(cmd)

    # find list
    lFiles = set()
    for row in out.split("\n"):
        # empty lines
        if len(row) < 2:
            continue
        # make sure to adapt to format
        f = row.split("/")
        if len(f) > 2:
            filename = "/".join(f[-2:])
        else:
            filename = "%s/%s"%(dataset,row)
        lFiles.add(filename)

    return lFiles

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: consistency.py  [ --book=pandaf/004" \
       + "  [ --dataset=SinglePhoton+Run2017B-31Mar2018-v1+MINIAOD [ --help ] ] ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','dataset=','verbose=','help']
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
book = "pandaf/010"
dataset = "SinglePhoton+Run2017B-31Mar2018-v1+MINIAOD"

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--book":
        book = arg
    if opt == "--dataset":
        dataset = arg

# say what we are looking at
print ''
print ' Book:    %s'%(book)
print ' Dataset: %s'%(dataset)
print ''

# split up thebook as usual
config = book.split("/")[0]
version = book.split("/")[1]

# find files and cataloged entries
files = findAllFiles(book,dataset)
lFiles = findLocalFiles(book,dataset)

# Calculate number of events

print ""
nTotal = 0
nMissing = 0
print ' Search for missing files (nT2: %d, mT3: %d).'%(len(files),len(lFiles))
for file in files:
    if file in lFiles:
        nTotal += 1
    else:
        nMissing += 1
        if verbose>0:
            print " missing: %s"%(file)

print " Number of files (total):   %d"%(nTotal)
print " Number of files (missing): %d"%(nMissing)

if nMissing == 0:
    sys.exit(0)
else:
    sys.exit(1)
