#---------------------------------------------------------------------------------------------------
# Python Module File to describe the lfn.
#
# lfn:  logical file name and all secrets it can tell you
#
# Author: C.Paus                                                                      (Jul 06, 2018)
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
"""
Class:  Lfn(fullFileName)

Given a full filename, construct the full information about this file.
"""
#---------------------------------------------------------------------------------------------------
class Lfn:
    "Logical filename that can be used to determine a lot of properties of the file history."
    #-----------------------------------------------------------------------------------------------
    # constructor to connect with existing setup
    #-----------------------------------------------------------------------------------------------
    def __init__(self,fullFileName):
        self.lfn = fullFileName[fullFileName.find("/store/user"):]
        f = self.lfn.split("/")
        self.fileId = f[-1].replace(".root","")
        self.dataset = f[-2]
        self.version = f[-3]
        self.config = f[-4]

    #-----------------------------------------------------------------------------------------------
    # present the full lfn information
    #-----------------------------------------------------------------------------------------------
    def show(self):
        print ' LFN:      %s'%(self.lfn)
        print ' -config:  %s'%(self.config)
        print ' -version: %s'%(self.version)
        print ' -dataset: %s'%(self.dataset)
        print ' -fileId:  %s'%(self.fileId)
