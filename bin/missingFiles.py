#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
# Find missing data and orphan data on disk.
#
# v1.0                                                                                  Jul 20, 2018
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import MySQLdb
import kdb
import rex

missing_output = 'missing.list'

def findAllLfns(book,dataset):

    print(" INFO - loading all lfns (Tier-2).")

    cmd = "cat %s/lfns/%s.lfns"%(os.getenv('KRAKEN_WORK'),dataset)
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    # find list
    lfns = {}
    for row in out.split("\n"):
        if len(row) < 3:
            continue
        f = row.split(" ")
        lfn = f[1]
        id = (f[1].split("/")[-1]).replace('.root','')
        lfns[id] = lfn

    return lfns

def findAllFiles(book,dataset):

    print(" INFO - loading all physical files (Tier-2).")

    cmd = "list /cms/store/user/paus/%s/%s "%(book,dataset) \
        + "|grep root"
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    # find list
    files = set()
    for row in out.split("\n"):
        if len(row) < 2:
            continue
        f = row.split(" ")
        id = (f[1].split("/")[-1]).replace('.root','')
        filename = id
        files.add(filename)

    return files

def findLocalFiles(book,dataset):

    print(" INFO - loading local physical files (Tier-3).")

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

def processDataset(book,dataset):
    # find files and cataloged entries
    lfns = findAllLfns(book,dataset)
    files = findAllFiles(book,dataset)
    lFiles = findLocalFiles(book,dataset)
    
    # Calculate number of events
    
    print("")
    nTotal = 0
    nMissing = 0
    print(' Search for missing files (nT2: %d, mT3: %d).'%(len(files),len(lFiles)))

    with open(missing_output,'a') as fM:
        for key in lfns:
            if key in files:
                nTotal += 1
            else:
                nMissing += 1
                print(" missing: %s"%(lfns[key]))
                # important to write the LFN not the full file name (no 'cms\')
                fM.write(f"/store/user/paus/{book}/{dataset}/{key}.root\n")

    print(" ==== Book: %s   Dataset: %s ===="%(book,dataset))
    print(" Number of lfns  (total):   %d"%(len(lfns)))
    print(" Number of files (total):   %d"%(nTotal))
    print(" Number of files (missing): %d"%(nMissing))

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: missingFiles.py  [ --book=pandaf/004" \
       + "  [ --pattern=Single [ --dataset=SinglePhoton+Run2017B-31Mar2018-v1+MINIAOD [ --help ] ] ] ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','dataset=','pattern=','verbose=','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# Set defaults for each command line parameter/option
verbose = 0
book = ""
dataset = ""
pattern = ""

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--book":
        book = arg
    if opt == "--dataset":
        dataset = arg
    if opt == "--pattern":
        pattern = arg

if book == "":
    print(" ERROR - book cannot be empty: %s"%(book))
    sys.exit(1)

# reset the missing file list
os.system(f"rm {missing_output}; touch {missing_output}")

# say what we are looking at
print('')
print(' Book:    %s'%(book))
if dataset != "":
    print(' Dataset: %s'%(dataset))
    print('')
    processDataset(book,dataset)        
else:
    print(' Found a list of datsets')
    print('')
    config = book.split("/")[0]
    version = book.split("/")[1]
    # list requests
    db = kdb.Kdb()
    for row in db.find_requests(config,version):

        dataset = "%s+%s+%s"%(row[0],row[1],row[2])
        if pattern in dataset:
            processDataset(book,dataset)        
