#---------------------------------------------------------------------------------------------------
# Python Module File to describe a Sample
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import os,sys

DEBUG = 0

#---------------------------------------------------------------------------------------------------
"""
Class:  Sample(dataset='undefined',dbs='instance=prod/global',
               useExistingLfns=False,useExistingJobs=False,useExistingSites=False)
Each sample can be described through this class
"""
#---------------------------------------------------------------------------------------------------
class Sample:
    "Description of a datasample to be produced using condor"

    #-----------------------------------------------------------------------------------------------
    # constructor
    #-----------------------------------------------------------------------------------------------
    def __init__(self,dataset='undefined',dbs='instance=prod/global',\
                     useExistingLfns=False,useExistingJobs=False,useExistingSites=False):

        # define command line parameters
        self.dataset = dataset
        self.dbs = dbs
        if dbs == 'local':
            self.dbs = os.environ.get('KRAKEN_CATALOG_INPUT','/home/cmsprod/catalog/t2mit')
        self.useExistingLfns = useExistingLfns
        self.useExistingJobs = useExistingJobs
        self.useExistingSites = useExistingSites

        # define the other contents
        self.nEvents = 0
        self.nEvtTotal = 0
        self.nMissingJobs = 0
        self.allLfns = {}
        self.allJobs = {}
        self.queuedJobs = {}               # queued jobs do NOT include the held ones
        self.heldJobs = {}                 # those are kept separate for further analysis
        self.noCatalogJobs = {}
        self.completedJobs = {}
        self.missingJobs = {}
        self.nFailedJobs = {}
        
        # fill contents
        self.loadAllLfns(self.makeLfnFile())
        self.loadAllJobs(self.makeJobFile())

        #self.loadSites(self.makeSiteFile())
        self.Sites = []

    #-----------------------------------------------------------------------------------------------
    # generate the lfn file and return it's location
    #-----------------------------------------------------------------------------------------------
    def makeLfnFile(self):

        lfnFile  = os.getenv('KRAKEN_WORK') + '/lfns/' + self.dataset + '.lfns'
    
        # give notice that file already exists
        if os.path.exists(lfnFile):
            print " INFO -- Lfn file found: %s. Someone already worked on this dataset." % lfnFile
    
        # remove what we need to to start clean
        cmd = 'rm -f ' +  lfnFile + '-TMP'
        os.system(cmd)
        
        # recreate if requested or not existing
        if not self.useExistingLfns or not os.path.exists(lfnFile) or os.stat(lfnFile).st_size == 0:
            cmd = 'input.py --dbs=' + self.dbs + ' --option=lfn --dataset=' + self.dataset \
                  + ' | sort -u > ' + lfnFile + '-TMP'
            print ' Input: ' + cmd
            os.system(cmd)
    
        # move the new file into the proper location
        if os.path.exists(lfnFile + '-TMP'):
            cmd = 'mv ' + lfnFile + '-TMP ' + lfnFile
            print ' Move: ' + cmd
            os.system(cmd)
    
        return lfnFile

    #-----------------------------------------------------------------------------------------------
    # generate the job file and return it's location
    #-----------------------------------------------------------------------------------------------
    def makeJobFile(self):

        jobFile  = os.getenv('KRAKEN_WORK') + '/jobs/' + self.dataset + '.jobs'
    
        # give notice that file already exists
        if os.path.exists(jobFile):
            print " INFO -- Job file found: %s. Someone already worked on this dataset." % jobFile
    
        # remove what we need to to start clean
        cmd = 'rm -f ' +  jobFile + '-TMP'
        os.system(cmd)
        
        # recreate if requested or not existing
        if not self.useExistingJobs or not os.path.exists(jobFile) or os.stat(jobFile).st_size == 0:
            cmd = 'input.py --dbs=' + self.dbs + ' --option=job --dataset=' + self.dataset \
                  + ' | sort -u > ' + jobFile + '-TMP'
            print ' Input: ' + cmd
            os.system(cmd)
    
        # move the new file into the proper location
        if os.path.exists(jobFile + '-TMP'):
            cmd = 'mv ' + jobFile + '-TMP ' + jobFile
            print ' Move: ' + cmd
            os.system(cmd)
    
        return jobFile
    
    #-----------------------------------------------------------------------------------------------
    # generate the sites file and return it's location
    #-----------------------------------------------------------------------------------------------
    def makeSiteFile(self):

        siteFile  = os.getenv('KRAKEN_WORK') + '/sites/' + self.dataset + '.sites'

        # check whether file exists already
        if os.path.exists(siteFile):
            print " INFO -- Site file found: %s. Someone already worked on this dataset." % siteFile

        # remove what we need to to start clean
        cmd = 'rm -f ' +  siteFile + '-TMP'
        os.system(cmd)
        
        # recreate if requested or not existing
        if not self.useExistingSites or not os.path.exists(siteFile) \
                or os.stat(siteFile).st_size == 0:
            cmd = 'sites.py --dbs=' + self.dbs + ' --dataset=' + self.dataset + ' > ' \
                + siteFile + '-TMP'
            print ' Sites: ' + cmd
            os.system(cmd)

        # move the new file into the proper location
        if os.path.exists(siteFile + '-TMP'):
            cmd = 'mv ' + siteFile + '-TMP ' + siteFile
            print ' Move: ' + cmd
            os.system(cmd)
    
        return siteFile

    #-----------------------------------------------------------------------------------------------
    # present the current samples
    #-----------------------------------------------------------------------------------------------
    def show(self):
        print ' ====  S a m p l e  ===='
        print ' Dataset       : ' + self.dataset
        print ' Dbs           : ' + self.dbs
        print ' NEvtTotal     : ' + str(self.nEvtTotal)
        print ' All Lfns      : ' + str(len(self.allLfns))
        print ' All Jobs      : ' + str(len(self.allJobs))
        print ' Queued Jobs   : ' + str(len(self.queuedJobs))
        print ' Held Jobs     : ' + str(len(self.heldJobs))
        print ' NoCatalog Jobs: ' + str(len(self.noCatalogJobs))
        print ' Completed Jobs: ' + str(len(self.completedJobs))
        print ' Missing Jobs  : ' + str(len(self.missingJobs))

    #-----------------------------------------------------------------------------------------------
    # return a string for all valid sites
    #-----------------------------------------------------------------------------------------------
    def getSitesString(self,pattern=''):
        siteString = ''
        for site in self.Sites:
            if pattern in site and not '_MSS' in site and not '_Buffer' in site:
                if siteString == '':
                    siteString = site
                else:
                    siteString += "," + site
        return siteString

    #-----------------------------------------------------------------------------------------------
    # load all lfns relevant to this task
    #-----------------------------------------------------------------------------------------------
    def loadAllLfns(self, lfnFile):
        
        print ' LFN file: %s\n'%(lfnFile)

        # initialize from scratch
        self.allLfns = {}
        self.nEvtTotal = 0
        # use the complete lfn file list
        cmd = 'cat ' + lfnFile
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            # get ride of empty or commented lines
            if line == '' or line[0] == '#':
                continue

            # decoding the input line
            f       = line.split() # splitting every blank
            lfn     = f[1]
            file    = (f[1].split("/")).pop()

            self.nEvents = int(f[2])
            self.nEvtTotal += self.nEvents
            if file in self.allLfns.keys():
                print " ERROR -- lfn appeared twice! This should never happen. IGNORE. (%s)"%file
                #print " ERROR -- lfn appeared twice! This should never happen. EXIT."
                #sys.exit(1)
            # add this lfn to the mix
            self.allLfns[file] = lfn

        if DEBUG > 0:
            print ''
            print ' TOTAL   - Lfns: %6d  [ Events: %9d ]'\
                %(len(self.allLfns),self.nEvtTotal)

    #-----------------------------------------------------------------------------------------------
    # load all jobs relevant to this task
    #-----------------------------------------------------------------------------------------------
    def loadAllJobs(self, jobFile):
        
        print ' JOB file: %s\n'%(jobFile)

        # initialize from scratch
        self.allJobs = {}
        self.nEvtTotal = 0
        # use the complete job file list
        cmd = 'cat ' + jobFile
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            # get ride of empty or commented lines
            if line == '' or line[0] == '#':
                continue

            # decoding the input line
            f       = line.split() # splitting every blank
            job     = f[1]
            file    = (f[1].split("/")).pop()

            self.nEvents = int(f[2])
            self.nEvtTotal += self.nEvents
            if file in self.allJobs.keys():
                print " ERROR -- job appeared twice! This should never happen. IGNORE. (%s)"%file
                #print " ERROR -- job appeared twice! This should never happen. EXIT."
                #sys.exit(1)
            # add this job to the mix
            self.allJobs[file] = job

        if DEBUG > 0:
            print ''
            print ' TOTAL   - Jobs: %6d  [ Events: %9d ]'\
                %(len(self.allJobs),self.nEvtTotal)

    #-----------------------------------------------------------------------------------------------
    # load sites for this sample/task
    #-----------------------------------------------------------------------------------------------
    def loadSites(self, siteFile):

        print ' SITES file: %s\n'%(siteFile)

        # initialize from scratch
        self.Sites = []
        # use the complete site file list
        cmd = 'cat ' + siteFile
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            # get ride of empty or commented lines
            if line == '' or line[0] == '#':
                continue

            # decoding the input line
            f = line.split(" ") # splitting every blank
            sites = f.pop()
            for site in sites.split(","):
                if site not in self.Sites:
                    self.Sites.append(site)

        if DEBUG > 0:
            siteString = ''
            if len(self.Sites)>0:
                siteString = self.Sites[0]
                for site in self.Sites[1:]:
                    siteString += "," + site
            print ' Sites: %2d: %s'%(len(self.Sites),siteString)

    #-----------------------------------------------------------------------------------------------
    # add one queued job to the list
    #-----------------------------------------------------------------------------------------------
    def addQueuedJob(self,file):

        if file not in self.allJobs.keys():
            print ' ERROR -- found queued job not in list of all jobs?! ->' + file + '<-'
            #print ' DEBUG - length: %d'%(len(self.allJobs))
        if file in self.queuedJobs.keys():
            print " ERROR -- queued job appeared twice! Should not happen but no danger. (%s)"%file
            #sys.exit(1)
        # add this job to the mix
        self.queuedJobs[file] = self.allJobs[file]

        return

    #-----------------------------------------------------------------------------------------------
    # add one held job to the list
    #-----------------------------------------------------------------------------------------------
    def addHeldJob(self,file):

        if file not in self.allJobs.keys():
            print ' ERROR -- found queued job not in list of all jobs?! ->' + file + '<-'
        if file in self.heldJobs.keys():
            print " ERROR -- held job appeared twice! Should not happen but no danger. (%s)"%file
            #sys.exit(1)
        # add this job to the mix
        self.heldJobs[file] = self.allJobs[file]

        return

    #-----------------------------------------------------------------------------------------------
    # reset the list of queued jobs
    #-----------------------------------------------------------------------------------------------
    def resetQueuedJobs(self):

        self.queuedJobs = {}

        return

    #-----------------------------------------------------------------------------------------------
    # reset the list of held jobs
    #-----------------------------------------------------------------------------------------------
    def resetHeldJobs(self):

        self.heldJobs = {}

        return

    #-----------------------------------------------------------------------------------------------
    # add all jobs so far completed but not yet cataloged relevant to this task
    # - they might fail cataloging but we assume they worked
    #-----------------------------------------------------------------------------------------------
    def addNoCatalogJob(self,file):

        if file not in self.allJobs.keys():
            print ' ERROR -- found queued job not in list of all jobs?! ->' + file + '<-'
        if file in self.noCatalogJobs.keys():
            print " ERROR -- noCatalog job appeared twice! Should not happen. EXIT (%s)"%file
            sys.exit(1)
        # add this job to the mix
        self.noCatalogJobs[file] = self.allJobs[file]

        return

    #-----------------------------------------------------------------------------------------------
    # add all jobs so far completed relevant to this task
    #-----------------------------------------------------------------------------------------------
    def addCompletedJob(self,file):

        if   file not in self.allJobs.keys():
            print ' ERROR -- found completed job not in list of all jobs?! ->' + file + '<-'
        elif file in self.completedJobs.keys():
            print " ERROR -- completed job appeared twice! Should not happen. EXIT (%s)"%file
            sys.exit(1)
        else:
            # add this job to the mix
            self.completedJobs[file] = self.allJobs[file]

        return

    #-----------------------------------------------------------------------------------------------
    # create the list with the number of failures of the given job
    #-----------------------------------------------------------------------------------------------
    def addNFailedJob(self,file,n):

        # add the number of failures of each failed job
        self.nFailedJobs["%s.root"%file] = n

        return

    #-----------------------------------------------------------------------------------------------
    # create the list of missing Jobs extracted fromt he previously created lists
    #-----------------------------------------------------------------------------------------------
    def createMissingJobs(self):

        # fill the remaining jobs from complete database
        self.missingJobs = {}
        for file,job in self.allJobs.iteritems():
            if file in self.missingJobs.keys():
                print " ERROR -- missing job appeared twice! Should never happen. EXIT. (%s)"%file
                sys.exit(1)
            # is it already completed?
            if file not in self.completedJobs.keys() and \
               file not in self.noCatalogJobs.keys() and \
               file not in self.queuedJobs.keys():
                # adding this one to the missing ones
                self.missingJobs[file] = job

        if DEBUG > 0:
            print ' MISSING - Jobs: %6d'%(len(self.missingJobs))
