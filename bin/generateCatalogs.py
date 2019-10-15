#!/usr/bin/env python
import os,re,pprint,subprocess,sys,datetime
import MySQLdb
import fileIds

DEBUG = int(os.environ.get('T2TOOLS_DEBUG',0))

DATA = os.environ.get('KRAKEN_SE_BASE','/cms/store/user/paus')
CATALOG = os.environ.get('KRAKEN_CATALOG_OUTPUT','/home/cmsprod/catalog/t2mit')
XRDSE = 'root://xrootd.cmsaf.mit.edu/'

Db = MySQLdb.connect(read_default_file="/etc/my.cnf",read_default_group="mysql",db="Bambu")
Cursor = Db.cursor()

usage = "\n   usage:  generateCatalogs.py  <book>  <pattern>  [ <nFilePerSet> ]\n"

#===================================================================================================
#  H E L P E R S
#===================================================================================================
def getFiles(book,dataset):
    # get all corresponding files

    version = book.split('/')[1]
    mitcfg = book.split('/')[0]

    # decode the dataset
    f = dataset.split('+')
    process = f[0]
    setup = f[1]
    tier = f[2]

    sql = "select FileName, NEvents from Files inner join Requests on " \
        + " Files.RequestId = Requests.RequestId inner join Datasets on " \
        + " Requests.DatasetId = Datasets.DatasetId where " \
        + " DatasetProcess = '%s' and DatasetSetup='%s' and DatasetTier='%s'"%(process,setup,tier) \
        + " and RequestConfig = '%s' and RequestVersion = '%s'"%(mitcfg,version)

    results = []
    try:
        # Execute the SQL command
        if DEBUG>0:
            print ' SQL: %s'%(sql)
        Cursor.execute(sql)
        if DEBUG>0:
            print ' SQL: fetch results'
        results = Cursor.fetchall()
        if DEBUG>0:
            print ' SQL: DONE'
    except:
        print 'ERROR(%s) - could not find request id.'%(sql)

    # found the request Id
    catalogedIds = fileIds.fileIds()
    for row in results:
        fileId = row[0]
        nEvents = int(row[1])

        catalogedId = fileIds.fileId(fileId,nEvents)
        catalogedIds.addFileId(catalogedId)

    return catalogedIds

def writeRawFile(rawFile,book,dataset):
    # get all corresponding files

    nFiles = 0

    try:
        if DEBUG>0:
            print ' Open Raw'
        with open(rawFile,'w') as fHandle:
            if DEBUG>0:
                print ' Get files'
            catalogedIds = getFiles(book,dataset)
    
            for id in sorted(catalogedIds.getIds()):
                fileId = catalogedIds.getFileId(id)
                nEvents = fileId.getNEvents()
                fileName = fileId.getFileName()
                fHandle.write('%s/store/user/paus/%s/%s/%s %d %d 1 1 1 1\n' \
                                  %(XRDSE,book,dataset,fileName,nEvents,nEvents))
                if DEBUG>0:
                    print ' file: %s'%(fileName)
                nFiles += 1
    except:
        print ' ERROR-- could not write raw file.'

    return nFiles

def makeCatalog(dir,nFilesPerSet):

    cmd = 'cat ' + dir + '/RawFiles.?? | grep root | sort -u'

    init = False
    iFileset = 0
    fileset = None

    filesetsOut = open(dir + '/Filesets','w')
    with open(dir + '/Files','w') as filesOut:
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            line = " ".join(str(line).split()).strip()
            f = line.split(' ')
            g = f[0].split('/')
            dataDir  = '/'.join(g[:-1])

            if not init:
                fileset = fileIds.fileIdSet('0000',dataDir)
                init = True

            fileName = g[-1]
            if len(f) != 7:
                print ' Length is not six: %d'%len(f)
                sys.exit(1)

            file = fileIds.fileId(fileName,int(f[1]),int(f[2]),int(f[3]),int(f[4]),int(f[5]),int(f[6]));

            if (fileset.nFiles()<nFilesPerSet):
                fileset.addFile(file)
            else:
                fileset.showShort(filesetsOut,DEBUG)
                fileset.showShortFiles(filesOut,DEBUG)
                iFileset = iFileset + 1
                name     = '%04d'%iFileset
                fileset.reset(name,dataDir)
                fileset.addFile(file)

        # complete what you started (will never be empty if init is set)
        if init:
            fileset.showShort(filesetsOut,DEBUG)
            fileset.showShortFiles(filesOut,DEBUG)
            iFileset = iFileset + 1

    filesetsOut.close()

#===================================================================================================
#  M A I N
#===================================================================================================
# make sure command line is complete
if len(sys.argv) > 4 or  len(sys.argv) < 3:
    print " ERROR -- number of arguments." + usage
    sys.exit(1)

# command line variables
book = sys.argv[1]
pattern = sys.argv[2]
nEventsPerSet = -1
if len(sys.argv) > 3:
    nEventsPerSet = sys.argv[3]

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

    print ' --> %s'%(dataset)

    catalogDir = '%s/%s/%s'%(CATALOG,book,dataset)
    if DEBUG>0:
        print ' Makedir'
    os.system('mkdir -p %s'%catalogDir)
    rawFile = '%s/RawFiles.00'%(catalogDir)
    if DEBUG>0:
        print ' Write Raw'
    nFiles = writeRawFile(rawFile,book,dataset)
    if nFiles<1:
        print ' INFO - no files found.'
        continue

    # decide how many files per fileset
    if DEBUG>0:
        print ' Make files*'
    if nEventsPerSet > 0:
        if DEBUG>0:
            print ' Making catalog'
        makeCatalog(catalogDir,nEventsPerSet)
        if DEBUG>0:
            print ' Making catalog DONE'
    else:
        if   nFiles > 400:
            makeCatalog(catalogDir,5)
        elif nFiles > 200:
            makeCatalog(catalogDir,3)
        else:
            makeCatalog(catalogDir,2)
