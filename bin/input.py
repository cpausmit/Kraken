#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
# Simple interface to command line DBS to prepare my processing task input files.
#---------------------------------------------------------------------------------------------------
import os,sys,types,string,re,getopt
import MySQLdb

# adding the certificate
cert = "--cert ~/.globus/usercert.pem --key ~/.globus/userkey.pem "

# Define string to explain usage of the script
usage =  "Usage: input.py --dataset=<name>\n"
usage += "                --option=[ jobs, lfns ]\n"
usage += "                [ --dbs= ]\n"
usage += "                [ --debug ]\n"
usage += "                [ --help ]\n"

# --------------------------------------------------------------------------------------------------
# H E L P E R S 
# --------------------------------------------------------------------------------------------------

##def generateContentFromCache(option,debug):
##    # use our local cache to generate the content
##
##    cmd = 'cat ' + db
##
##    if debug:
##        print(" CMD: " + cmd)
##
##    content = []
##    for line in os.popen(cmd).readlines():
##        line    = line[:-1]
##        f       = line.split()
##        block   = f[0]
##        lfn     = f[1]
##        nEvents = int(f[2])
##    
##        f       = lfn.split("/")
##        file    = f[-1]
##
##        if nEvents != 0:
##            content.append(printLine(option,nEvents,block,lfn))
##
##    return content
    
def generateContent(dataset,option,debug):
    # use officical dbs commands to generate the content

    f = dataset.split("/")
    process = f[1]
    setup = f[2]
    tier = f[3]

    # Open database connection
    db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
    # Prepare a cursor object using cursor() method
    cursor = db.cursor()
    
    sql = "select Blocks.BlockName, Lfns.PathName, Lfns.FileName, Lfns.NEvents"\
        + " from Lfns inner join Blocks on " \
        + " Lfns.BlockId = Blocks.BlockId inner join Datasets on " \
        + " Datasets.DatasetId = Blocks.DatasetId where " \
        + " DatasetProcess = '%s' and DatasetSetup='%s' and DatasetTier='%s'"\
        %(process,setup,tier)

    if debug:
        print(" SQL: " + sql)

    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print(" ERROR (%s): unable to fetch data."%(sql))
        sys.exit(0)

    content = []
    for row in results:
        nEvents = int(row[3])
        bName = dataset+'#'+row[0]
        pName = row[1]
        fName = row[2]
        fNameR = fName + '.root'
        if nEvents>0:
            if option == 'job':
                content.append("%s %s %d"%(fName,pName+'/'+fNameR,nEvents))
            elif option == 'lfn':
                content.append("%s %s %d"%(bName,pName+'/'+fNameR,nEvents))
                

    return content
    
def generateContentFromPanda(dataset,dbs,option,debug):
    # use the catalog
    
    f = dataset.split("=")
    book = f[0] + "/" + f[1]
    dataset = f[2]

    with open("%s/%s/%s/Filesets"%(dbs,book,dataset),"r") as f:
        inputFsets = f.read()
    f = inputFsets.split(" ")
    if len(f) > 1:
        pName = inputFsets.split(" ")[1]
        pName = re.sub(r'root://.*/(/store/.*)',r'\1',pName)
    else:
        print(' ERROR -- no filesets found.')
        sys.exit(1)

    with open("%s/%s/%s/Files"%(dbs,book,dataset),"r") as f:
        inputFiles = f.read()

    content = []

    nEvent = 0
    fset = ''
    last = ''
    files = ''
    nEvents = ''
    for line in inputFiles.split("\n"):
        line = ' '.join(line.split())
        f = line.split(" ")
        if len(f) > 2:
            fset = f[0]
            fName = f[1]
            nEvent = int(f[2])

            if option == 'lfn':
                content.append("%s %s %d"%(fset,pName+'/'+fName,nEvent))

            if fset != last:
                if last != '':
                    if nEvents>0:
                        if option == 'job':
                            content.append("%s %s %d"%(last,pName+'/'+last+'.root',nEvents))
                files = fName
                nEvents = nEvent
            else:
                files += ',' + fName
                nEvents += nEvent
               
            last = fset
        else:
            continue

    if files != '':
        if nEvents>0 and option == 'job':
            content.append("%s %s %d"%(fset,pName+'/'+fset+'.root',nEvents))

    return content
    
# --------------------------------------------------------------------------------------------------
# M A I N
# --------------------------------------------------------------------------------------------------
# Define the valid options which can be specified and check out the command line
valid = ['db=','dbs=','dataset=','option=','debug','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex: 
    print(usage)
    print(str(ex))
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# Set defaults for each option
db = None
dbs = 'prod/global'
dataset = None
option = 'lfn'
private = False
debug = False

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--dbs":
        dbs = arg
    if opt == "--dataset":
        dataset = arg
        if not '=' in dataset and dataset[0] != '/':
            dataset = '/' + dataset.replace('+','/')
    if opt == "--option":
        option  = arg
    if opt == "--debug":
        debug = True

# Deal with obvious problems
if dataset == None:
    cmd = "--dataset=  required parameter not provided."
    print(" Runtime error: %s"%cmd)
    sys.exit(1)

# initialize the content of the file
content = []

if 'catalog' in dbs:
    content = generateContentFromPanda(dataset,dbs,option,debug)
else:
    content = generateContent(dataset,option,debug)

# here is where we print
for line in content:
    if line != '':
        print(line)
