#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------
# Test consistency between the data on disk, the data registered in
# the Kraken database and the data in the catalogs.
#
# v1.0                                                                                  Jul 12, 2018
#---------------------------------------------------------------------------------------------------
import os,sys,socket,getopt,time
import MySQLdb
import rex

CATALOG = "/home/tier3/cmsprod/catalog/t2mit"
EXEC_FILE = "/home/tier3/cmsprod/Tools/Kraken/fixFiles"
DYNAMO_SERVER = "t3desk000.mit.edu"

def findAllFiles(dir):

    print(" INFO - loading all physical files on T2.")

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
            size = int((row.split(" ")[0]).split(":")[1])
            filename = "/".join((row.split(" ")[-1]).split('/')[-2:])
            
            files[filename] = size

            if size < 10:
                print(" ERROR - zero size file found: " + filename)
    
    return files

def findCatalogFiles(config,version):

    # say what we do
    print(" INFO - loading all files from the catalog (%s)."%(CATALOG))

    # concatenate all files from the requested book
    cmd  = "cat %s/%s/%s/*/RawFiles* |tr -s ' ' > /tmp/Files"%(CATALOG,config,version)
    #print(" CMD> " + cmd)
    os.system(cmd)

    # read the file produced
    cfiles = {}
    with open("/tmp/Files","r") as fH:
        data = fH.read()
    for line in data.split("\n"):
        if len(line)>4:
            cfile = "/".join((line.split(" ")[0]).split("/")[-2:])
            size = int(line.split(" ")[1])
            cfiles[cfile] = size

    return files

def findAllKrakenFiles(config,version):

    print(" INFO - loading all files from Kraken database.")

    # all possibly produced lfns
    sql = "select Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,Blocks.BlockName,Lfns.FileName" \
        + " from Datasets" \
        + " inner join Lfns on Lfns.DatasetId = Datasets.DatasetId" \
        + " inner join Blocks on Blocks.BlockId = Lfns.BlockId"

    #print(" SLQ: " + sql)
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print(" ERROR (%s): select failed."%(sql))
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
    #print(" SLQ: " + sql)
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print(" ERROR (%s): select failed."%(sql))
        sys.exit(0)
    
    klfns = {}
    for row in results:
        dataset = row[0]+'+'+row[1]+'+'+row[2]
        file_name = row[3]
        klfn = "%s/%s.root"%(dataset,file_name)
        klfns[klfn] = -1      # for now no size comparison planned

    return klfns

def findAllDynamoFiles(config,version,site="T2_US_MIT"):

    # say what we do
    print(" INFO - loading all %s files from Dynamo database."%(site))

    # spawn a dynamo process
    cmd  = "%s/bin/makeListOfFileFromInventory.py --book %s/%s"%(os.getenv('KRAKEN_BASE'),config,version)
    cmd += " --site %s"%(site)
    #print(" CMD> " + cmd)
    os.system("dynamo '%s' 2> /tmp/last_dynamo.log"%(cmd))

    # read the file produced
    dlfns = {}
    # extract the unique file name
    inventory =  "/tmp/.inventory_%s_%s_%s.tmp"%(site,config,version)
    try:
        with open(inventory,"r") as fH:
            data = fH.read()
        for line in data.split("\n"):
            if len(line)>10:
                dlfn = "/".join(line.split("/")[-2:])
                size = int(line.split(" ")[0])
                dlfns[dlfn] = size
    except:
        print(" WARNING - file list (%s) not available."%(inventory))

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
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# Make sure we run on the correct server
if socket.gethostname().lower() != DYNAMO_SERVER:
    print(usage)
    print(" ERROR -- You are working on: %s\n"%(socket.gethostname().lower()))
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# Set defaults for each command line parameter/option
debug = 0
book = "nanodp/F01"

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--book":
        book = arg

config = book.split("/")[0]
version = book.split("/")[1]

print("")
print("   CONSISTENCY FOR  ---- Book:%s ----"%book)
print(" XoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoXoX")
print("")

# Open database connection
db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
# Prepare a cursor object using cursor() method
cursor = db.cursor()

# find files and cataloged entries
files = findAllFiles("/cms/store/user/paus/%s"%(book))
cfiles = findCatalogFiles(config,version)
klfns = findAllKrakenFiles(config,version)

# disconnect from server
db.close()

# CONSISTENCY -- Files versus Catalog

# find missing files
print("")
print("   PHYSICAL FILE T2 VS CATALOG")
print(" ...............................")
with open("%s.catalog-missing"%EXEC_FILE,"w") as fH:
    nMissing = 0
    print(' Search for missing files (nP: %d, mC: %d).'%(len(files),len(cfiles)))
    for cfile in cfiles:
        if cfile in files:
            continue
        else:
            nMissing += 1
            print(" missing: %s"%(cfile))
            fH.write("removeFile.py --exe --fileName /cms/store/user/paus/%s/%s\n"%(book,cfiles[cfile]))
    print(" missing total: %d"%(nMissing))

print("")
print("   PHYSICAL FILE T2 VS BAMBUDB")
print(" ...............................")
with open("%s.kraken-missing"%EXEC_FILE,"w") as fH:
    nMissing = 0
    print(' Search for missing files (nP: %d, mL: %d).'%(len(files),len(klfns)))
    for klfn in klfns:
        if klfn in files:
            continue
        else:
            nMissing += 1
            #print(" missing: %s"%(klfn))
            fH.write("removeFile.py --exe --fileName /cms/store/user/paus/%s/%s\n"%(book,klfn))
    print(" missing total: %d"%(nMissing))

# find orphan files

with open("%s.kraken-orphan"%EXEC_FILE,"w") as fH:
    nOrphan = 0
    print(' Search for orphan files (nP: %d, mL: %d).'%(len(files),len(klfns)))
    for file in files:
        if file in klfns:
            continue
        else:
            nOrphan += 1
            fH.write("/cms/store/user/paus/%s/%s\n"%(book,file))
    print(" orphan total: %d"%(nOrphan))
    if nOrphan > 0:
        cmd=f"cat {EXEC_FILE}.kraken-orphan /home/tier3/cmsprod/cms/work/fibs/checkFile.list | sort -u > tmp.list; mv tmp.list /home/tier3/cmsprod/cms/work/fibs/checkFile.list"
        print(f"{cmd}")
        os.system(f"fibsLock.py --config checkFile --cmd=\"{cmd}\"; wc /home/tier3/cmsprod/cms/work/fibs/checkFile.list")
