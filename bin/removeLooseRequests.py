#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Find requests that are not 
#
# v1.0                                                                                  Sep 19, 2014
#---------------------------------------------------------------------------------------------------
import sys,os,subprocess,getopt,time
import MySQLdb

def removeRequest(cursor,id,config,version,py):
    sql  = "delete from Requests where "
    sql += "DatasetId=%d and RequestConfig='%s' and RequestVersion='%s' and RequestPy='%s' ;"\
        %(id,config,version,py)
    
    if debug>0:
        print ' delete: ' + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print " Error (%s): unable to delete data."%(sql)

def removeDataset(cursor,id):
    sql  = "delete from Datasets where DatasetId=%d;"%(id)
    
    if debug>0:
        print ' delete: ' + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except:
        print " Error (%s): unable to delete data."%(sql)

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage  = "\n"
usage += " Usage: findLooseRequests.py  [ --help ]\n\n"

# Define the valid options which can be specified and check out the command line
valid = ['help']
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

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)

# Open database connection
db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")

# Prepare a cursor object using cursor() method
cursor = db.cursor()

if not os.path.exists(".unknownIds"):
    # find requestIds from Files
    sql = "select distinct RequestId from Files";
    print " SQL: " + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " Error (%s): unable to fetch data."%(sql)
        sys.exit(0)
    
    allIds = []
    for row in results:
        id = int(row[0])
        allIds.append(id)
    
    # find known requestIds
    sql = "select RequestId from Requests";
    print " SQL: " + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print " Error (%s): unable to fetch data."%(sql)
        sys.exit(0)
    
    knownIds = []
    for row in results:
        id = int(row[0])
        if id in knownIds:
            pass
        else:
            knownIds.append(id)
    
    unknownIds = []
    i = 0
    for id in allIds:
        if id in knownIds:
            pass
        else:
            unknownIds.append(id)
            print ' Unknown: %s'%(id)
        i += 1
else:
    unknownIds = []
    with open(".unknownIds",'r') as f:
        for line in f:
            line = line[:-1]
            f = line.split(' ')
            unknownIds.append(int(f[0]))
    
i = 0
for id in unknownIds:

    #print " Unknown request id: %s"%(id)

    # find known requestIds
    sql = "delete from Files where Files.RequestId = %d"%(int(id));
    print ' SQL: ' + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
        db.commit()
    except:
        print " ERROR (%s): deletion failed."%(sql)
        sys.exit(0)

# disconnect from server
db.close()
