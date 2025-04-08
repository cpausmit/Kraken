#!/usr/bin/env python

import os
import sys
import rex
import requests
import json
import time
import pprint

myRex = rex.Rex()
base = os.environ.get('KRAKEN_SE_BASE','/cms/store/user/paus')

def findFileSizes(config,version,dataset):

    fileSizes = {}
    cmd = "t2tools.py --action ls --source %s/%s/%s/%s |grep root"%(base,config,version,dataset)
    (rc,out,err) = myRex.executeLocalAction(cmd)
    for line in out.split('\n'):
        if len(line.split(' '))>1:
            size = (line.split(' ')[0]).split(':')[1]
            fileName = (line.split('/')[-1]).split('.')[0]
            fileSizes[fileName] = int(size)

    return fileSizes

def getRequestId(cursor,config,version,dataset):
    # extract the unique request id this file is part of

    requestId = -1
    datasetId = -1

    # decode the dataset
    f = dataset.split('+')
    if len(f) < 3:
        print " ERROR - dataset name not correctly formed: " + dataset
        sys.exit(0)
    process = f[0]
    setup = f[1]
    tier = f[2]

    sql = "select RequestId, Datasets.DatasetId from Requests inner join Datasets on " \
        + " Datasets.DatasetId = Requests.DatasetId where " \
        + " DatasetProcess = '%s' and DatasetSetup='%s' and DatasetTier='%s'"%(process,setup,tier) \
        + " and RequestConfig = '%s' and RequestVersion = '%s'"%(config,version)

    #print ' SQL - ' + sql

    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print 'ERROR(%s) - could not find request id.'%(sql)

    # found the request Id
    for row in results:
        requestId = int(row[0])
        datasetId = int(row[1])

    return (requestId, datasetId)

def updateDatabaseEntry(cursor,requestId,fileName,size):

    sql = "update Files set SizeBytes = %d where RequestId = '%s' and FileName = '%s';" \
        %(size,requestId,fileName)
    #print ' SQL: ' + sql
    try:
        # Execute the SQL command
        cursor.execute(sql)
    except MySQLdb.IntegrityError as e:
        if not e[0] == 1062:
            print 'ERROR(%s) - could not update file.'%(sql)
            raise
        else:
            print " WARNING -- error update." 

if __name__ == '__main__':
    import MySQLdb    
    from argparse import ArgumentParser
    
    # getting the commend line parameters
    parser = ArgumentParser(description = 'Generate Bambu database inventory.')
    parser.add_argument('--config', '-c', metavar = 'CONFIG', dest = 'config', default = 'pandaf', help = 'Panda configuration.')
    parser.add_argument('--version', '-v', metavar = 'VERSION', dest = 'version', default = '010', help = 'Panda version.')
    parser.add_argument('--dataset', '-d', metavar = 'DATASET', dest = 'dataset', help = 'Panda dataset name.')
    args = parser.parse_args()
    sys.argv = []

    # get the file sizes in a dictionary
    fileSizes = findFileSizes(args.config,args.version,args.dataset)

    # make connection with database
    conn = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
    cursor = conn.cursor()
    (requestId, datasetId) = getRequestId(cursor,args.config,args.version,args.dataset)

    # now loop through the dictionary of filesizes and update the database entries
    print " [%s,%s]: N:%d %s"%(args.config,args.version,len(fileSizes),args.dataset)
    for fileName in fileSizes.keys():
        updateDatabaseEntry(cursor,requestId,fileName,fileSizes[fileName])
