#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Find missing data and orphan data on disk.
#
# v1.0                                                                                  Sep 19, 2014
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import MySQLdb
import rex

def findAllFiles(book,dataset):

    print " INFO - loading all physical files."

    cmd = "gfal-ls gsiftp://se01.cmsaf.mit.edu:2811/cms/store/user/paus/%s/%s "%(book,dataset) + "|grep root"
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

def findAllKrakenFiles(config,version):

    print " INFO - loading all files from Kraken database."

    # find all files cataloged at some point
    sql = "select Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,Files.FileName,Files.NEvents" \
        + " from Requests" \
        + " inner join Datasets on Requests.DatasetId = Datasets.DatasetId" \
        + " inner join Files on Files.RequestId = Requests.RequestId where" \
        + " Requests.RequestConfig = '%s' and"%config \
        + " Requests.RequestVersion = '%s'"%version
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " ERROR (%s): select failed."%(sql)
        sys.exit(0)
    
    klfns = {}
    for row in results:
        dataset = row[0]+'+'+row[1]+'+'+row[2]
        filename = row[3]
        klfn = "%s/%s.root"%(dataset,filename)
        klfns[klfn] = int(row[4])

    return klfns

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: consistency.py  [ --book=pandaf/004  [ --dataset=SinglePhoton+Run2017B-31Mar2018-v1+MINIAOD [ --help ] ] ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['book=','dataset=','help']
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

config = book.split("/")[0]
version = book.split("/")[1]

# Open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
# Prepare a cursor object using cursor() method
cursor = db.cursor()

# find files and cataloged entries
files = findAllFiles(book,dataset)
klfns = findAllKrakenFiles(config,version)

# disconnect from server
db.close()

# Calculate number of events

print ""
nTotal = 0
print ' Search for missing files (nP: %d, mL: %d).'%(len(files),len(klfns))
for file in files:
    if file in klfns:
        nTotal += klfns[file]
    else:
        print " ERROR: did not find this klfn for existing file %s"%(file)

print " Total number of events: %d"%(nTotal)
