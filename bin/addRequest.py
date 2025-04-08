#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
# Add a new dataset production request into the Bambu database.
#
# v1.0                                                                                  Sep 19, 2014
#---------------------------------------------------------------------------------------------------
import sys,os,subprocess,getopt,time
import MySQLdb

def testLocalSetup(dataset,config,version,dbs,py,delete,debug=0):
    # test all relevant components and exit is something is off

    # check the input parameters
    if dataset == '':
        print(' Error - no dataset specified. EXIT!\n')
        print(usage)
        sys.exit(1)
    if config == '':
        print(' Error - no config specified. EXIT!\n')
        print (usage)
        sys.exit(1)
    if version == '':
        print(' Error - no version specified. EXIT!\n')
        print(usage)
        sys.exit(1)
    if py == '':
        print(' Error - no py specified. EXIT!\n')
        print(usage)
        sys.exit(1)

    # check that the dataset exists in bambu database
    if delete<1:
        #pass
        cmd = 'addDataset.py --exec --dataset=' + dataset + ' --dbs=' + dbs
        if debug>0:
            print(' CMD: ' + cmd)
        rc = os.system(cmd)
        if rc != 0:
            print(' Error - dataset seems not to be valid. EXIT!\n')
            sys.exit(1)
    else:
        print(' Info - this is a deletion, so we do not add the sample to the database.')

def removeRequest(cursor,id,config,version,py):
    sql  = "delete from Requests where "
    sql += "DatasetId=%d and RequestConfig='%s' and RequestVersion='%s' and RequestPy='%s' ;"\
        %(id,config,version,py)
    
    if debug>0:
        print(' delete: ' + sql)
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print(" Error (%s): unable to delete data."%(sql))

def removeDataset(cursor,id):
    sql  = "delete from Datasets where DatasetId=%d;"%(id)
    
    if debug>0:
        print(' delete: ' + sql)
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print(" Error (%s): unable to delete data."%(sql))

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: addRequest.py  --dataset=<name>\n"
usage += "                       --config=<name>\n"
usage += "                       --version=<name>\n"
usage += "                     [ --py=mc ]\n"
usage += "                     [ --delete=0: 1-delete request, 2-delete request and dset ]\n"
usage += "                     [ --dbs=prod/global ]\n"
usage += "                     [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['dataset=','config=','version=',"dbs=",'py=','delete=','debug=','help']
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
debug = 0
delete = 0
dataset = ''
config = ''
version = ''
dbs = 'prod/global'
py = 'mc'

isPanda = False

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--dataset":
        dataset = arg
        if dataset[0] != '/':
            dataset = '/' + dataset.replace('+','/')
        if '=' in dataset:
            isPanda = True
    if opt == "--config":
        config = arg
    if opt == "--version":
        version = arg
    if opt == "--dbs":
        dbs = arg
    if opt == "--py":
        py = arg
    if opt == "--delete":
        delete = int(arg)
    if opt == "--debug":
        debug = int(arg)

testLocalSetup(dataset,config,version,dbs,py,delete,debug)

# Open database connection
db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")

# Prepare a cursor object using cursor() method
cursor = db.cursor()

# Decompose dataset into the three pieces (process, setup, tier)
f = dataset.split('/')
process = f[1]
setup   = f[2]
tier    = f[3]
if process == "mc":
    process = f[2]
    setup   = f[3]
    tier    = f[4]

# First get the dataset id
sql = "select DatasetId from Datasets where " \
    + "DatasetProcess='%s' and DatasetSetup='%s' and DatasetTier='%s';"%(process,setup,tier)
if debug>0:
    print(' select: ' + sql)
try:
    # Execute the SQL command
    cursor.execute(sql)
    results = cursor.fetchall()
except:
    print(" Error (%s): unable to fetch data."%(sql))
    sys.exit(0)

if len(results) != 1:
    if delete<1:
        print(' Requested dataset not well defined, check database (nEntries=%d).'%(len(results)))
    else:
        print(' Dataset not in database, deletion not needed.')
    sys.exit(0)
else:
    id = int(results[0][0])
    if debug>0:
        print(' DatasetId=%d.'%(id))

# Check whether this processing request already exists in the database

sql  = "select * from Requests where "
sql += "DatasetId=%d and RequestConfig='%s' and RequestVersion='%s' and RequestPy='%s' ;"\
       %(id,config,version,py)
if debug>0:
    print(' select: ' + sql)
try:
    # Execute the SQL command
    cursor.execute(sql)
    results = cursor.fetchall()
except:
    print(" Error (%s): unable to fetch data."%(sql))
    sys.exit(0)

if len(results) > 0:
    print(' Request exists already in database. Do not insert again (nEntries=%d).'%(len(results)))
    if delete>0:
        removeRequest(cursor,id,config,version,py)
    if delete==1:
        sys.exit(0)
else:
    pass

# order of deletion is important to be least vulnerable to database problems

if delete > 1:
    removeDataset(cursor,id)
    sys.exit(0)

# now insert if this is not a deletion request

if delete<1:
    # Prepare SQL query to insert a new record into the database.
    sql = "insert into Requests(DatasetId, RequestConfig, RequestVersion, RequestPy)" + \
          " values(%d,'%s','%s','%s');"%(id,config,version,py)
    
    if debug>0:
        print(' insert: ' + sql)
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print(' ERROR -- insert failed, rolling back.')
        # disconnect from server
        db.close()
        print(' Request was NOT inserted into the database (%s,%s,%s,%s).'\
            %(dataset,config,version,py))
        sys.exit(1)
        
    print(' Request successfully inserted into the database (%s,%s,%s,%s).'\
        %(dataset,config,version,py))

# disconnect from server
db.close()
