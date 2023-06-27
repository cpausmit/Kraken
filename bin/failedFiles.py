#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Find all failed files from the public_html records.
#
# v1.0                                                                                  Feb 23, 2021
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import MySQLdb
import rex

DATA = os.environ.get('KRAKEN_SE_BASE','/cms/store/user/paus')
TRUNC = '/local/cmsprod/Kraken/agents/reviewd'

def findFiles(book,dataset):
    # very important to only look at files that are newer than the ones we counted already

    print(" INFO - analyzing book:%s  dataset:%s."%(book,dataset))

    cmd = "ls -1t %s/%s/%s/*.err "%(TRUNC,book,dataset)
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    # find list
    files = set()
    for row in out.split("\n"):
        if len(row) < 2:
            continue
        fileName = (row.split('/')[-1]).split('.')[0]
        if 'ncounts' in fileName: # only consider files that were not yet analyzed
            print(" Found the counts file: %s (%s) --> BREAK"%(row,fileName))
            break
        print(" Adding file: %s"%(fileName))
        files.add(fileName)

    return files

def findExistingFailedFiles(book,dataset):

    print(" INFO - find existing failures:  book:%s  dataset:%s."%(book,dataset))
    fileName = "%s/%s/%s/ncounts.err"%(TRUNC,book,dataset)

    data = ''
    if os.path.exists(fileName):
        with open(fileName,"r") as file:
            data = file.read()

    # make a list
    nerrors = {}
    for row in data.split("\n"):
        if len(row) < 2:
            continue
        filename = row.split(' ')[0]
        nerrors[filename] = int(row.split(' ')[1])

    return nerrors

def writeFailedFiles(book,dataset,nerrors):

    print(" INFO - write failures:  book:%s  dataset:%s."%(book,dataset))
    fileName = "%s/%s/%s/ncounts.err"%(TRUNC,book,dataset)
    print(" INFO - file: %s."%(fileName))

    with open(fileName,"w") as file:
        for key,ncount in nerrors.items():
            file.write("%s %d\n"%(key,ncount))

    ## make sure to copy this file to the 
    #dir = '/local/cmsprod/Kraken/agents/reviewd/%s/%s'%(book,dataset)
    #cmd = 'cp %s %s'%(fileName,dir)
    #os.system(cmd)

    return

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: failedFiles.py  [ --book=nanoao/510" \
       + "  [ --pattern=SingleElectron+Run2017F-31Mar2018-v1+MINIAOD [ --help ] ] ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','pattern=','verbose=','help']
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
book = "nanoao/512"
pattern = "BdToPiMuNu_BMuonFilter_SoftQCDnonD_TuneCP5_13TeV-pythia8-evtgen+RunIIFall17MiniAODv2-PU2017_12Apr2018_94X_mc2017_realistic_v14-v1+MINIAODSIM"

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--book":
        book = arg
    if opt == "--pattern":
        pattern = arg

# say what we are looking at
print('')
print(' Book:    %s'%(book))
print(' Pattern: %s'%(pattern))
print('')

# make list of datasets in given book
cmd = 'list ' +  DATA + "/" + book
if pattern != "":
    cmd += "| grep %s"%(pattern)

allDatasets = []
for line in os.popen(cmd).readlines():
    f = (line[:-1].split("/"))[-1:]
    dataset = "/".join(f)
    allDatasets.append(dataset)

print(' Number of datasets found: %d'%(len(allDatasets)))

# loop over all matching datasets
for dataset in allDatasets:

    # find files and cataloged entries
    files = findFiles(book,dataset)
    nerrors = findExistingFailedFiles(book,dataset)

    # update the file counts of the files that were found
    for f in files:
        if f in nerrors:
            nerrors[f] += 1
        else:
            nerrors[f] = 1
        
    # re-write the file and update the time stamp if we found something
    if len(files) > 0:
        print(" Writing a new file of error counts.")
        writeFailedFiles(book,dataset,nerrors)
    else:
        print(" No update needed.")
