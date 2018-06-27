#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Find requests that are used in the Files catalog table but are not available in the Requests
# table and delete those entries from the Files table with the unknown Ids.
#
# v1.0                                                                                  Sep 19, 2014
#---------------------------------------------------------------------------------------------------
import sys,os,subprocess,getopt,time
import MySQLdb

def findAllIds(db,cursor):

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

    return allIds

def findKnownIds(db,cursor):

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
        knownIds.append(id)

    return knownIds

def findUnknownIds(allIds,knownIds):

    # find unknown Ids (they are in all but not in known)
    unknownIds = []
    for id in allIds:
        if id in knownIds:
            pass
        else:
            unknownIds.append(id)
            print ' Unknown: %s'%(id)

    return unknownIds

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

allIds = findAllIds(db,cursor)
knownIds = findKnownIds(db,cursor)
unknownIds = findUnknownIds(allIds,knownIds)

for id in unknownIds:

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
