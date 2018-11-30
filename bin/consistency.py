#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Find missing data and orphan data on disk.
#
# v1.0                                                                                  Jul 12, 2018
#---------------------------------------------------------------------------------------------------
import sys,os,socket,getopt,time
import MySQLdb
import rex

EXEC_FILE = "/home/cmsprod/Tools/Kraken/fixFiles"
DYNAMO_SERVER = "t3serv009.mit.edu"

def findAllFiles(dir):

    print " INFO - loading all physical files."

    cmd = "list %s/* "%(dir) + "|grep root"
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)


    with open(".sizes","w") as fH:
        # find list
        files = {}
        for row in out.split("\n"):
            if len(row) < 2:
                continue

            fH.write(row+'\n')
            size = row.split(":")[0]
            filename = "/".join((row.split(" ")[-1]).split('/')[-2:])
    
            files[filename] = size
    
    return files

def findAllKrakenFiles(config,version):

    print " INFO - loading all files from Kraken database."

    # all possibly produced lfns
    sql = "select Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,Blocks.BlockName,Lfns.FileName" \
        + " from Datasets" \
        + " inner join Lfns on Lfns.DatasetId = Datasets.DatasetId" \
        + " inner join Blocks on Blocks.BlockId = Lfns.BlockId"

    #print " SLQ: " + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " ERROR (%s): select failed."%(sql)
        sys.exit(0)
    
    with open(".blocks","w") as fH:
        for row in results:
            dataset = row[0]+'+'+row[1]+'+'+row[2]
            block_name = row[3]
            file_name = row[4]
            klfn = "%s/%s.root"%(dataset,file_name)
            fH.write("%s %s\n"%(block_name,klfn))

    # find all files cataloged at this point
    sql = "select Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,Files.FileName" \
        + " from Requests" \
        + " inner join Datasets on Requests.DatasetId = Datasets.DatasetId" \
        + " inner join Files on Files.RequestId = Requests.RequestId where" \
        + " Requests.RequestConfig = '%s' and"%config \
        + " Requests.RequestVersion = '%s'"%version
    #print " SLQ: " + sql
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
        file_name = row[3]
        klfn = "%s/%s.root"%(dataset,file_name)
        #print " KLFN: %s"%(klfn)
        klfns[klfn] = -1      # for now no size comparison planned

    return klfns

def findAllDynamoFiles(config,version):

    # say what we do
    print " INFO - loading all files from Dynamo database."

    # spawn a dynamo process
    cmd = "%s/bin/makeListOfFileFromInventory.py --book %s/%s"%(os.getenv('KRAKEN_BASE'),config,version)
    #print " CMD> " + cmd
    os.system("dynamo '%s' 2> /dev/null"%(cmd))

    # read the file produced
    dlfns = {}
    # extract the unique file name
    inventory =  "/tmp/.inventory_%s_%s.tmp"%(config,version)
    try:
        with open(inventory,"r") as fH:
            data = fH.read()
        for line in data.split("\n"):
            if len(line)>10:
                dlfn = "/".join(line.split("/")[-2:])
                size = line.split(" ")[0]
                dlfns[dlfn] = size
    except:
        print " WARNING - file list (%s) not available."%(inventory)

    return dlfns

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage = "\n" \
    + " Usage: consistency.py  [ --book=pandaf/004 [ --help ] ]\n\n" \
    + "        this script has to run on the dynamo server node (%s)\n\n"%(DYNAMO_SERVER)

# Define the valid options which can be specified and check out the command line
valid = ['book=','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# Make sure we run on the correct server
if socket.gethostname().lower() != DYNAMO_SERVER:
    print usage
    print " ERROR -- You are working on: %s\n"%(socket.gethostname().lower())
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

print ""
print "   CONSISTENCY FOR  ---- Book:%s ----"%book
print " XoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoX"
print ""


# Open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
# Prepare a cursor object using cursor() method
cursor = db.cursor()

# find files and cataloged entries
files = findAllFiles("/cms/store/user/paus/%s"%(book))
klfns = findAllKrakenFiles(config,version)
dlfns = findAllDynamoFiles(config,version)

# disconnect from server
db.close()

# CONSISTENCY -- Files versus BambuDb

# find missing files
print ""
print "   PHYSICAL FILE VS BAMBUDB"
print " ............................."
with open("%s.kraken-missing"%EXEC_FILE,"w") as fH:
    nMissing = 0
    print ' Search for missing files (nP: %d, mL: %d).'%(len(files),len(klfns))
    for klfn in klfns:
        if klfn in files:
            continue
        else:
            nMissing += 1
            #print " missing: %s"%(klfn)
            fH.write("removeFile.py --exe --fileName /cms/store/user/paus/%s/%s\n"%(book,klfn))
    print " missing total: %d"%(nMissing)

# find orphan files

with open("%s.kraken-orphan"%EXEC_FILE,"w") as fH:
    nOrphan = 0
    print ' Search for orphan files (nP: %d, mL: %d).'%(len(files),len(klfns))
    for file in files:
        if file in klfns:
            continue
        else:
            nOrphan += 1
            #print " orphan: %s"%(file)
            fH.write("checkFile.py /cms/store/user/paus/%s/%s\n"%(book,file))
    print " orphan total: %d"%(nOrphan)

# CONSISTENCY -- BambuDB versus Dynamo

print ""
print "   BAMBUDB VERSUS DYNAMO"
print " ............................."

# find missing files
with open("%s.dynamo-missing"%EXEC_FILE,"w") as fH:
    nMissing = 0
    print ' Search for missing files (nD: %d, mB: %d).'%(len(dlfns),len(klfns))
    for klfn in klfns:
        if klfn in dlfns:
            continue
        else:
            nMissing += 1
            #print " missing: %s"%(klfn)
            fH.write("dynamo-inject-one-file /cms/store/user/paus/%s/%s\n"%(book,klfn))
    print " missing total: %d"%(nMissing)
    
# find orphan files
with open("%s.dynamo-orphan"%EXEC_FILE,"w") as fH:
    nOrphan = 0
    print ' Search for orphan files (nD: %d, mB: %d).'%(len(dlfns),len(klfns))
    for dlfn in dlfns:
        if dlfn in klfns:
            continue
        else:
            nOrphan += 1
            #print " orphan: %s"%(dlfn)
            fH.write("dynamo-delete-one-file /cms/store/user/paus/%s/%s\n"%(book,dlfn))
    print " orphan total: %d"%(nOrphan)
