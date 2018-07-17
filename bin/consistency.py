#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Find missing data and orphan data on disk.
#
# v1.0                                                                                  Sep 19, 2014
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import MySQLdb
import rex

EXEC_FILE = "/home/cmsprod/Tools/Kraken/fixMissingFiles"

def findAllFiles(dir):

    print " INFO - loading all physical files."

    cmd = "list %s/* "%(dir) + "|grep root"
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    # find list
    files = set()
    for row in out.split("\n"):
        if len(row) < 2:
            continue
        filename = "/".join((row.split(" ")[-1]).split('/')[-2:])
        files.add(filename)

    return files

def findAllCatalogedFiles(config,version):

    print " INFO - loading all files from Kraken database."

    # find all files cataloged at some point
    sql = "select Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,Files.FileName" \
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
    
    lfns = set()
    for row in results:
        dataset = row[0]+'+'+row[1]+'+'+row[2]
        filename = row[3]
        lfn = "%s/%s.root"%(dataset,filename)
        #print " LFN: %s"%(lfn)
        lfns.add(lfn)

    return lfns

def findAllDynamoFiles(config,version):

    # say what we do
    print " INFO - loading all files from Dynamo database."

    # spawn a dynamo process
    cmd = "%s/bin/makeListOfFileFromInventory.py --book %s/%s"%(os.getenv('KRAKEN_BASE'),config,version)
    os.system("dynamo '%s' 2> /dev/null"%(cmd))

    # read the fle produced
    dlfns = set()
    # extract the unique file name
    try:
        with open("/tmp/.inventory_%s_%s.tmp"%(config,version),"r") as fH:
            data = fH.read()
        for line in data.split("\n"):
            if len(line)>10:
                dlfn = "/".join(line.split("/")[-2:])
                dlfns.add(dlfn)
    except:
        print " WARNING - file list (%s) not available."%(fileName)

    ## find all files injected into dynamo
    #dlfns = set()
    #for dataset in inventory.datasets.itervalues():
    #    if dataset.name.startswith('%s/%s'%(config,version)):
    #        for dlfn in dataset.files:
    #            dlfn = "/".join((dlfn.lfn).split("/")[-2:])
    #            dlfns.add(dlfn)

    return dlfns

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: consistency.py  [ --book=pandaf/004 [ --help ] ]\n\n"

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

# Open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
# Prepare a cursor object using cursor() method
cursor = db.cursor()

# find files and cataloged entries
files = findAllFiles("/cms/store/user/paus/%s"%(book))
lfns = findAllCatalogedFiles(config,version)
dlfns = findAllDynamoFiles(config,version)

# disconnect from server
db.close()

# CONSISTENCY -- Files versus BambuDb

# find missing files
print ""
print " XXXX oooo XXXX oooo XXXX oooo XXXX"
print "   PHYSICAL FILE VS BAMBUDB"
print " XXXX oooo XXXX oooo XXXX oooo XXXX"
with open("%s.kraken"%EXEC_FILE,"w") as fH:
    nMissing = 0
    print ' Search for missing files (nP: %d, mL: %d).'%(len(files),len(lfns))
    for lfn in lfns:
        if lfn in files:
            continue
        else:
            nMissing += 1
            print " missing: %s"%(lfn)
            fH.write("removeFile.py --exe --fileName /cms/store/user/paus/%s/%s\n"%(book,lfn))
    print " missing total: %d"%(nMissing)

# find orphan files
nOrphan = 0
print ' Search for orphan files (nP: %d, mL: %d).'%(len(files),len(lfns))
for file in files:
    if file in lfns:
        continue
    else:
        nOrphan += 1
        print " orphan: %s"%(file)
print " orphan total: %d"%(nOrphan)

# CONSISTENCY -- BambuDB versus Dynamo

print ""
print " XXXX oooo XXXX oooo XXXX oooo XXXX"
print "   BAMBUDB VERSUS DYNAMO"
print " XXXX oooo XXXX oooo XXXX oooo XXXX"

# find missing files
with open("%s.dynamo"%EXEC_FILE,"w") as fH:
    nMissing = 0
    print ' Search for missing files (nD: %d, mB: %d).'%(len(dlfns),len(lfns))
    for lfn in lfns:
        if lfn in dlfns:
            continue
        else:
            nMissing += 1
            print " missing: %s"%(lfn)
            fH.write("dynamo-inject-one-file /cms/store/user/paus/%s/%s\n"%(book,lfn))
    print " missing total: %d"%(nMissing)
    
# find orphan files
with open("%s.dynamo-orphan"%EXEC_FILE,"w") as fH:
    nOrphan = 0
    print ' Search for orphan files (nD: %d, mB: %d).'%(len(dlfns),len(lfns))
    for dlfn in dlfns:
        if dlfn in lfns:
            continue
        else:
            nOrphan += 1
            print " orphan: %s"%(dlfn)
            fH.write("dynamo-delete-one-file /cms/store/user/paus/%s/%s\n"%(book,dlfn))
    print " orphan total: %d"%(nOrphan)
