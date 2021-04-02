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
TRUNC = '/home/cmsprod/public_html/Kraken/agents/reviewd'

def findFiles(book,dataset):

    print(" INFO - analyzing book:%s  dataset:%s."%(book,dataset))

    cmd = "ls -1t %s/%s/%s/*.err "%(TRUNC,book,dataset)
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    # find list
    files = set()
    for row in out.split("\n"):
        if len(row) < 2:
            continue
        file_name = (row.split('/')[-1]).split('.')[0]
        if 'ncounts' in file_name: # only consider files that were not yet analyzed
            break
        files.add(file_name)

    return files

def findExistingFailedFiles(book,dataset):

    print(" INFO - find existing failures:  book:%s  dataset:%s."%(book,dataset))
    file_name = "%s/%s/%s/ncounts.err"%(TRUNC,book,dataset)

    data = ''
    if os.path.exists(file_name):
        with open(file_name,"r") as file:
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
    file_name = "%s/%s/%s/ncounts.err"%(TRUNC,book,dataset)
    print(" INFO - file: %s."%(file_name))

    with open(file_name,"w") as file:
        for key,ncount in nerrors.items():
            file.write("%s %d\n"%(key,ncount))

    dir = '/local/cmsprod/Kraken/agents/reviewd/%s/%s'%(book,dataset)
    cmd = 'cp %s %s'%(file_name,dir)
    os.system(cmd)

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
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# Set defaults for each command line parameter/option
verbose = 0
book = "nanoao/510"
pattern = "SingleElectron+Run2017F-31Mar2018-v1+MINIAOD"

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--book":
        book = arg
    if opt == "--pattern":
        pattern = arg

# say what we are looking at
print ''
print ' Book:    %s'%(book)
print ' Pattern: %s'%(pattern)
print ''

# make list of datasets
cmd = 'list ' +  DATA + "/" + book
if pattern != "":
    cmd += "| grep %s"%(pattern)

allDatasets = []
for line in os.popen(cmd).readlines():
    f = (line[:-1].split("/"))[-1:]
    dataset = "/".join(f)
    allDatasets.append(dataset)

print ' Number of datasets found: %d'%(len(allDatasets))

# loop over all matching datasets
for dataset in allDatasets:

    # find files and cataloged entries
    files = findFiles(book,dataset)
    print(files)
    nerrors = findExistingFailedFiles(book,dataset)
    for file in files:
        if file in nerrors:
            nerrors[file] += 1
        else:
            nerrors[file] = 1
        
    writeFailedFiles(book,dataset,nerrors)
