#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
#
# Check catalogs and remove any suspicious entries. There is no cataloging of files done here.
#
# - find all files from the lfn file used for production
# - find all files in the catalog
# - find all files on disk
#
# Remove any file that is not coherent in any way from the catalog and if needed from disk.
#
#---------------------------------------------------------------------------------------------------
import os,sys,subprocess
import fileIds

DEBUG = int(os.environ.get('T2TOOLS_DEBUG',0))
DIR = "/cms/store/user/paus"

#---------------------------------------------------------------------------------------------------
#  H E L P E R S
#---------------------------------------------------------------------------------------------------
def removeFileIdsFromDisk(book,dataset,fileIds):
    # take a given list of patterns and remove all related files from disk

    for badFileId in sorted(fileIds):
        if badFileId != '':
            cmd = " t2tools.py --action=rm --source=" + DIR + '/' \
                + book + '/' + dataset + '/' + badFileId + '*' 
            print " RM - from disk: " + cmd
            os.system(cmd)

def cleanCatalogFile(file,book,dataset,patterns):
    # take a given file and remove all lines that match any of the given patterns

    print " Clean file: %s"%(file)
    if DEBUG>0:
        print " Remove: "
    badWords = []
    for badWord in sorted(patterns):
        if badWord != '':
            badWords.append(badWord)
            print "  " + badWord
            #cmd = " t2tools.py --action=rm --source=" + DIR + '/' \
            #    + book + '/' + dataset + '/' + badWord + '*' 
            #print " RM - from disk: " + cmd
            #os.system(cmd)

    lRemove = False
    out = ''
    with open(file) as fH:
        for line in fH:
            if not any(badWord in line for badWord in badWords):
                out += line
            else:
                lRemove = True
                print " RM - from ctlg: " + line[:-1]

    # was there something removed?
    if lRemove:
        with open(file,'w') as fH:
            fH.write(out)

    return

def removePatternsFromCatalog(catalog,book,dataset,patterns):
    # clean the existing catalog files and remove the files matching the given pattern

    directory = catalog + '/' + book + '/' + dataset

    for filename in os.listdir(directory):
        if "Files" in filename: 
            cleanCatalogFile(directory + '/' + filename,book,dataset,patterns)

def loadCatalog(catalog,book,dataset):
    # load the unique file ids of the existing catalog for existence checks (careful)

    mitcfg = book.split("/")[0]
    version = book.split("/")[1]

    catalogedIds = fileIds.fileIds()

    # first make sure the catalog is compact

    rc = 0
    cmd = "grep root " + catalog + '/' + book + '/' + dataset + '/RawFiles.00'
    list = cmd.split(" ")
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode

    if rc != 0:
        print " ERROR -- %d"%(rc)
        print out
        print err
        #sys.exit(1)
    
    for line in out.split("\n"):
        f = line.split(" ")
        if len(f) > 2:
            name = f[0]
            nEvents = int(f[1])
            catalogedId = fileIds.fileId(name,nEvents)
            catalogedIds.addFileId(catalogedId)

    return catalogedIds
    
    
def loadLfns(dataset):

    lfnIds = fileIds.fileIds()

    # find the correct file

    lfnFile = "/home/cmsprod/cms/jobs/lfns/" + dataset + ".lfns"
    if DEBUG>0:
        print " LFN file: " + lfnFile
    
    rc = 0
    cmd = "cat " + lfnFile
    list = cmd.split(" ")
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode

    if rc != 0:
        print " ERROR -- %d"%(rc)
        print out
        print err
        #sys.exit(1)
    
    for line in out.split("\n"):
        f = line.split(" ")
        if len(f) > 2:
            name = f[1]
            nEvents = int(f[2])
            lfnId = fileIds.fileId(name,nEvents)
            lfnIds.addFileId(lfnId)

    return lfnIds

def loadFilesFromDisk(book,dataset):

    fileOnDiskIds = fileIds.fileIds()

    # list all files from the giben directory
    cmd = 'list ' + DIR + "/" + book + "/" + dataset
    if DEBUG>0:
        print " CMD (loadFilesFromDisk): " + cmd
    
    rc = 0
    list = cmd.split(" ")
    p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode

    if rc != 0:
        print " ERROR -- %d"%(rc)
        print out
        print err
        #sys.exit(1)
    
    for line in out.split("\n"):
        if '.root' in line:
            f = line.split(" ")
            if len(f) > 1:
                name = f[1]
                nEvents = -1
                fileOnDiskId = fileIds.fileId(name,nEvents)
                fileOnDiskIds.addFileId(fileOnDiskId)

    return fileOnDiskIds

#---------------------------------------------------------------------------------------------------
#  M A I N
#---------------------------------------------------------------------------------------------------
catalog = os.environ.get('KRAKEN_CATALOG_INPUT','/home/cmsprod/catalog/t2mit')

book = sys.argv[1]
pattern = ''
if len(sys.argv) > 2:
    pattern = sys.argv[2]

# hi, here we are!
os.system("date")

# make a list of all directories
allDatasets = []
if pattern == '':
    print ' Find all datasets.'
else:
    print ' Find all datasets matching %s.'%(pattern)

cmd = 'list ' + DIR + "/" + book
if pattern != "":
    cmd += "| grep %s"%(pattern)

if DEBUG>0:
    print ' CMD: ' + cmd

for line in os.popen(cmd).readlines():
    f = (line[:-1].split("/"))[-1:]
    dataset = "/".join(f)
    allDatasets.append(dataset)
    if DEBUG>1:
        print ' Found Dataset: ' + dataset
print ' Number of datasets found: %d'%(len(allDatasets))


for dataset in allDatasets:
    print ' Process Dataset: ' + dataset

    # load all information we need
    #-----------------------------

    # the original lfns from DBS (our cache)
    lfnIds = loadLfns(dataset)

    # the files that we have right now on disk (Tier-2)
    fileOnDiskIds = loadFilesFromDisk(book,dataset)

    # all files in the catalog
    catalogedIds = loadCatalog(catalog,book,dataset)

    # perform all checks
    #-------------------

    # check whether we loaded correctly
    uniqueLfnIds = lfnIds.getIds()
    if len(uniqueLfnIds) > 0:
        if DEBUG>0:
            print '  --> %d lfns'%(len(uniqueLfnIds))        
    else:
        print ' ERROR - looks like the lfns are empty: %s'%(dataset)

    # check for duplicated Ids in the catalog and remove them
    duplicatedIds = catalogedIds.getDuplicatedIds()

    # check whether event counts are good
    incompleteIds = {}
    uniqueIds = catalogedIds.getIds()
    for id in sorted(uniqueIds):
        nEventsLfn = (lfnIds.getFileId(id)).nEvents
        nEvents = (catalogedIds.getFileId(id)).nEvents
        if nEvents != nEventsLfn:
            if DEBUG>0:
                print " ERROR(%s) -- count is different  %d  !=  %d"%(id,nEventsLfn,nEvents)
            incompleteIds[id] = 1

    # check whether file in catalog is on disk
    virtualIds = {}
    for id in sorted(uniqueIds):
        if not fileOnDiskIds.getFileId(id):
            virtualIds[id] = 1

    # check list of all fileIds that are bad (duplicate or wrong counts) and are also on disk
    toDeletionIds = {}
    for id in sorted(incompleteIds):
        if fileOnDiskIds.getFileId(id):
            toDeletionIds[id] = 1
    for id in sorted(duplicatedIds):
        if fileOnDiskIds.getFileId(id):
            toDeletionIds[id] = 1

    # report what we have found
    #--------------------------

    print '  --> %6d/%6d/%6d  allLfns/unique/onDisk - %s'%\
        (len(uniqueLfnIds),len(uniqueIds),fileOnDiskIds.getSize(),dataset)
    print '  --> %6d/%6d/%6d/%6d  duplicated/incomplete/virtual/toDelete -  WORK TO BE DONE'%\
        (len(duplicatedIds),len(incompleteIds),len(virtualIds),len(toDeletionIds))

    # cross checking

    print "\n ==== Start cross checks ====\n"

    # find file that are on disk but not in catalog
    print ' ondisk '
    for fileName in sorted(fileOnDiskIds.getIds()):
        if not (fileName in uniqueIds):
            print " MISSING IN CATALOG: %s"%(fileName)
        else:
            pass
            #print " OK: %s"%(fileName)
            #print " OK: %s"%(fileName)
        if not (fileName in uniqueLfnIds):
            print " ERROR UNKNOWN LFN: %s"%(fileName)

    # find file that are in the catalog but not on disk
    print ' in catalog '
    for fileName in sorted(uniqueIds):
        if not (fileName in fileOnDiskIds.getIds()):
            print " MISSING ON DISK: %s"%(fileName)
        else:
            pass
            #print " OK: %s"%(fileName)
        if not (fileName in uniqueLfnIds):
            print " ERROR UNKNOWN LFN: %s"%(fileName)

    print "\n ==== Finished cross checks ====\n"


    # here is where we fix everything
    #--------------------------------

    print "\n ==== Start fixes ====\n"
    
    # fix the catalog
    if len(duplicatedIds) > 0:
        print '\n checkCatalogs.py -- Cleanup the duplicate files from catalogs'
        removePatternsFromCatalog(catalog,book,dataset,duplicatedIds)
    if len(incompleteIds) > 0:
        print '\n checkCatalogs.py -- Cleanup the incomplete files from catalogs'
        removePatternsFromCatalog(catalog,book,dataset,incompleteIds)
    if len(virtualIds) > 0:
        print '\n checkCatalogs.py -- Cleanup the virtual files from catalogs'
        removePatternsFromCatalog(catalog,book,dataset,virtualIds)
    
    # fix the files on disk
    if len(toDeletionIds) > 0:
        print '\n checkCatalogs.py -- Cleanup the bad files on disk'
        removeFileIdsFromDisk(book,dataset,toDeletionIds)

    print "\n ==== Finish fixes ====\n"

    os.system("checkDirectory.py /cms/store/user/paus/%s/%s"%(book,dataset))
