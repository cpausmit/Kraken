#---------------------------------------------------------------------------------------------------
# Python Module File to describe metaData, fileId, fileIds and fileIdSet
#
# metaData:  basic meta data of a of data file(s). Can be added.
#
# fileId:    the smallest unit of a bunch of data which are accounted for on a hard drive.
#
# fileIds:   a bunch of fileIds, they are supposed to be unique.
#
# FileIdset: a set of files which contain the same type of events and are stored in the same
#            directory. Filesets are created to reduce the number of 'processing jobs' when talking
#            about greater collections of data. The number of files per fileset is therefore
#            crucial.
#
# Author: C.Paus                                                                      (Oct 10, 2008)
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
"""
Class:  metaData(nEvents,nLumiSecs,minRun,minLumiSecInMinRun,maxRun,maxLumiSecInMaxRun)

A given bunch of events, may it be a file or just 10 events or even an entire dataset can be
specified by minimal set of meta data. This class defines this set of meta data and the methods
useful for dealing with it.
"""
#---------------------------------------------------------------------------------------------------
class metaData:
    "A Meta Data description of a bunch of Bambu events (any data/MC events can be described)."
    #-----------------------------------------------------------------------------------------------
    # constructor to connect with existing setup
    #-----------------------------------------------------------------------------------------------
    def __init__(self,nEvents,
                 nLumiSecs=0,minRun=999999999,minLumiSecInMinRun=0,maxRun=0,maxLumiSecInMaxRun=0):
        self.nEvents            = nEvents
        self.nLumiSecs          = nLumiSecs
        self.minRun             = minRun
        self.minLumiSecInMinRun = minLumiSecInMinRun
        self.maxRun             = maxRun
        self.maxLumiSecInMaxRun = maxLumiSecInMaxRun
    #-----------------------------------------------------------------------------------------------
    # present the current set of Meta Data
    #-----------------------------------------------------------------------------------------------
    def show(self):
        print(' Number of:    events %9d  lumi sections %d'%(self.nEvents,self.nLumiSecs))
        print(' Lowest  data: run    %9d  lumi section  %9d'%(self.minRun,self.minLumiSecInMinRun))
        print(' Highest data: run    %9d  lumi section  %9d'%(self.maxRun,self.maxLumiSecInMaxRun))
    #-----------------------------------------------------------------------------------------------
    # adding meta data
    #-----------------------------------------------------------------------------------------------
    def add(self,right):
        self.nEvents           += right.nEvents
        self.nLumiSecs         += right.nLumiSecs
        if self.minRun > right.minRun or \
               (self.minRun == right.minRun and \
                self.minLumiSecInMinRun > right.minLumiSecInMinRun):
            self.minRun             = right.minRun
            self.minLumiSecInMinRun = right.minLumiSecInMinRun
        if self.maxRun < right.maxRun or \
               (self.maxRun == right.maxRun and \
                self.maxLumiSecInMaxRun < right.maxLumiSecInMaxRun):
            self.maxRun             = right.maxRun
            self.maxLumiSecInMaxRun = right.maxLumiSecInMaxRun

#---------------------------------------------------------------------------------------------------
"""
Class:  FileId(name,nEvents,nLumiSecs,minRun,minLumiSecInMinRun,maxRun,maxLumiSecInMaxRun)

A given bunch of events, may it be a file or just 10 events or even an entire dataset can be
specified by minimal set of meta data. This class defines this set of meta data and the methods
useful for dealing with it.
"""
#---------------------------------------------------------------------------------------------------
class fileId(metaData):
    '''Class to work with unique fileIds and the number of events they correspond to.'''

    def __init__(self,name,nEvents,
                 nLumiSecs=0,minRun=999999999,minLumiSecInMinRun=0,maxRun=0,maxLumiSecInMaxRun=0):
        metaData.__init__(self,nEvents,nLumiSecs,minRun,minLumiSecInMinRun,maxRun,maxLumiSecInMaxRun)

        # initialize the fileId correctly while extracting the proper name
        if '/' in name:
            name = (name.split("/"))[-1]
        if '.root' in name:
            name = name.replace(".root","")
        if '_tmp' in name:
            name = name.replace("_tmp","")
        self.name = name

    def getNEvents(self):
        # return how many events in this fileId

        return self.nEvents

    def getName(self):
        # return the file name corresponding to this Id

        return self.name

    def getFileName(self):
        # return the file name corresponding to this Id

        return self.name + '.root'

    def getTmpName(self):
        # return the temporary file name corresponding to this Id

        return self.name + '_tmp.root'

    def show(self):
        print(' ==== Meta Data for File %s ===='%(self.name))
        metaData.show(self)

    def showShort(self,filesetName,oFile=0,debug=1):
        line = "%s %40s %9d %9d %9d %6d %9d %6d"%(filesetName,self.name+'.root', \
                                                  self.nEvents,self.nLumiSecs, \
                                                  self.minRun,self.minLumiSecInMinRun, \
                                                  self.maxRun,self.maxLumiSecInMaxRun)
        if debug > 0:
            print(line)
        oFile.write(line+'\n')

#---------------------------------------------------------------------------------------------------
"""
Class:  fileIds()

This class is a smart container for a bunch of fileIds to keep track of duplicates and facilitate
work with these fileIds
"""
#---------------------------------------------------------------------------------------------------
class fileIds:
    '''Class to work with a bunch of unique fileIds.'''

    def __init__(self):
        self.ids = {}
        self.duplicatedIds = {}

    def addFileId(self,fileId):
        # safely add another Id to the dictionary

        if fileId.name in self.duplicatedIds:
            print(' ERROR -- fileId appeared at least twice already (%s).'%(fileId.name))
            return

        if fileId.name in self.ids:
            print(' ERROR -- fileId is already in our dictionary (%s).'%(fileId.name))
            self.ids[fileId.name].show()
            fileId.show()
            print(' ----')
            self.duplicatedIds[fileId.name] = fileId
            # delete the key from the initial list
            del self.ids[fileId.name]            
        else:
            self.ids[fileId.name] = fileId

    def getDuplicatedIds(self):
        # access to dictionary of duplicated file Ids

        return self.duplicatedIds

    def getIds(self):
        # access to dictionary of unique file Ids

        return self.ids


    def getFileId(self,name):
        # access full information of a particular fileId

        fileId = None
        if name in self.ids:
            fileId = self.ids[name]
        else:
            print(' ERROR -- fileId is already in our dictionary (%s).'%(name))

        return fileId

    def getSize(self):
        # access to the size of the dictionary of good file Ids

        return len(self.ids)

    def show(self):
        # show our fileIds ordered by ids

        print(' List of Ids appearing once')
        for id in sorted(self.ids):
            print(" %s - %d"%(id,self.ids[id].nEvents))
        print(' List of duplicated Ids')
        for id in sorted(self.duplicatedIds):
            print(" %s - %d"%(id,self.duplicatedIds[id].nEvents))

    def showDuplicates(self):
        # show our fileIds ordered by ids

        if len(self.duplicatedIds) > 0:
            print(' List of duplicated Ids')
        else:
            print(' No duplicated Ids')
            
        for id in sorted(self.duplicatedIds):
            print(" %s - %d"%(id,self.duplicatedIds[id].nEvents))


#---------------------------------------------------------------------------------------------------
"""
Class:  Fileset(name)

This class defines the Meta Data relevant for a set of files. They will be extracted from the files
being added to the set.
"""
#---------------------------------------------------------------------------------------------------
class fileIdSet(metaData):
    "A Meta Data description of a set of Bambu Files (any data/MC file can be described this way)."

    name               = 'undefined'
    dir                = ''
    fileList           = []

    def __init__(self,name,dir):
        # constructor to connect with existing setup

        metaData.__init__(self,0)
        self.name = name
        self.dir  = dir
        self.fileList  = []

    def reset(self,name,dir):
        # resetting it to zero

        metaData.__init__(self,0)
        self.name     = name
        self.dir      = dir
        self.fileList = []

    def show(self):
        # present the contents of the fileset in various forms

        print(' ==== Meta Data for Fileset %s ===='%(self.name))
        metaData.show(self)

    def showShort(self,oFile=0,debug=1):
        # present the contents of the fileset in various forms

        line = "%s %40s %9d %9d %9d %6d %9d %6d"%(self.name,self.dir,self.nEvents,self.nLumiSecs, \
                                                      self.minRun,self.minLumiSecInMinRun, \
                                                      self.maxRun,self.maxLumiSecInMaxRun)
        if debug > 0:
            print(line)
        oFile.write(line+'\n')

    def showShortFiles(self,oFile=0,debug=1):
        # present the contents of the fileset in various forms
        for file in self.fileList:
            file.showShort(self.name,oFile,debug)

    def addFile(self,file):
        # add one more file

        self.add(file)
        self.fileList.append(file)

    def nFiles(self):
        # how many files in this set

        return len(self.fileList)

#---------------------------------------------------------------------------------------------------
"""
Class:  lfn(fileId,datasetsId,blockId,path)

A given bunch of events, may it be a file or just 10 events or even an entire dataset can be
specified by minimal set of meta data. This class defines this set of meta data and the methods
useful for dealing with it.
"""
#---------------------------------------------------------------------------------------------------
class lfn:
    "A Meta Data description of a bunch of Bambu events (any data/MC events can be described)."
    #-----------------------------------------------------------------------------------------------
    # constructor to connect with existing setup
    #-----------------------------------------------------------------------------------------------
    def __init__(self,fileId,blockName,pathName):
        self.fileId = fileId
        self.blockName = blockName
        self.pathName = pathName

    def show(self):
        # present the contents of the lfn
        self.fileId.show()
        print('   block: %s  path: %s'%(self.blockName,self.pathName))
