#---------------------------------------------------------------------------------------------------
# Python Module File to describe task
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import os,sys,re,string,socket
import rex

DEBUG = 0

#---------------------------------------------------------------------------------------------------
"""
Class:  Request(scheduler=None,sample=None,config='filefi',version='046',py='data')
A request will have to specify the configuration, version and python configuration file to be
applied to the also given a scheduler and a sample.
"""
#---------------------------------------------------------------------------------------------------
class Request:
    "Description of a request for a specific sample processing."

    #-----------------------------------------------------------------------------------------------
    # constructor
    #-----------------------------------------------------------------------------------------------
    def __init__(self,scheduler=None,sample=None,config='filefi',version='046',py='data'):
        
        self.base = os.getenv('KRAKEN_SE_BASE')

        self.scheduler = scheduler
        self.sample = sample
        self.config = config
        self.version = version
        self.py = py

        self.loadQueuedJobs()
        self.loadHeldJobs()
        self.loadCompletedJobs()
        self.sample.createMissingJobs()

    #-----------------------------------------------------------------------------------------------
    # load all jobs so far completed relevant to this task
    #-----------------------------------------------------------------------------------------------
    def loadCompletedJobs(self):

        # initialize from scratch
        path = self.base + '/' + self.config + '/' + self.version + '/' \
            + self.sample.dataset
        # first fully checked files
        cmd = 'list ' + path + '  2> /dev/null | grep root'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split()
            file = (f[1].split("/")).pop()
            self.sample.addCompletedJob(file)
        # now also look at the temporary files (not yet cataloged)
        cmd = 'list ' + path + '/crab_*/  2> /dev/null | grep _tmp.root'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split()
            file = (f[1].split("/")).pop()
            file = file.replace('_tmp','')
            self.sample.addNoCatalogJob(file)
        if DEBUG > 0:
            print ' NOCATAL - Jobs: %6d'%(len(self.sample.noCatalogJobs))
            print ' DONE    - Jobs: %6d'%(len(self.sample.completedJobs))

    #-----------------------------------------------------------------------------------------------
    # load all jobs that are presently queued
    #-----------------------------------------------------------------------------------------------
    def loadQueuedJobs(self):

        # initialize from scratch
        self.sample.resetQueuedJobs()

        path = self.base + '/' + self.config + '/' + self.version + '/' + self.sample.dataset
        pattern = "%s %s %s %s"%(self.config,self.version,self.py,self.sample.dataset)
        cmd = 'condor_q ' + self.scheduler.user \
            + ' -constraint JobStatus!=5 -format \'%s\n\' Args 2> /dev/null|grep \'' + pattern + '\''

        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
                + ' \"' + cmd + '\"'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split(' ')
            file = f[5] + '.root'
            self.sample.addQueuedJob(file)
        if DEBUG > 0:
            print ' QUEUED  - Jobs: %6d'%(len(self.sample.queuedJobs))

    #-----------------------------------------------------------------------------------------------
    # load all jobs that are presently queued but in held state
    #-----------------------------------------------------------------------------------------------
    def loadHeldJobs(self):

        # initialize from scratch
        self.sample.resetHeldJobs()

        path = self.base + '/' + self.config + '/' + self.version + '/' \
            + self.sample.dataset
        pattern = "%s %s %s %s"%(self.config,self.version,self.py,self.sample.dataset)
        cmd = 'condor_q ' + self.scheduler.user \
            + ' -constraint JobStatus==5 -format \'%s\n\' Args 2> /dev/null|grep \'' + pattern + '\''

        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
                + ' \"' + cmd + '\"'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split(' ')
            file = f[5] + '.root'
            self.sample.addHeldJob(file)

        if DEBUG > 0:
            print ' HELD    - Jobs: %6d'%(len(self.sample.heldJobs))

#---------------------------------------------------------------------------------------------------
"""
Class:  Scheduler(host='submit.mit.edu',user='paus')
Each sample can be described through this class
"""
#---------------------------------------------------------------------------------------------------
class Scheduler:
    "Description of a scheduler using condor"

    #-----------------------------------------------------------------------------------------------
    # constructor
    #-----------------------------------------------------------------------------------------------
    def __init__(self,host='submit.mit.edu',user='cmsprod',base=''):

        self.here = socket.gethostname()
        self.update(host,user,base)


    #-----------------------------------------------------------------------------------------------
    # execute a condor command on the given scheduler
    #-----------------------------------------------------------------------------------------------
    def executeCondorCmd(self,cmd='condor_q',output=False):

        print ' execute condor command: %s'%(cmd)

        myRx = rex.Rex(self.host,self.user);
        irc = 0

        if not self.isLocal():
            (irc,rc,out,err) = myRx.executeAction(cmd)
            if (irc != 0 or rc != 0):
                print ' ERROR -- IRC: %d'%(irc) 
        else:
            (rc,out,err) = myRx.executeLocalAction(cmd)
            
        if (irc != 0 or rc != 0):
            print ' ERROR -- RC: %d'%(rc) 
            print ' ERROR -- ERR:\n%s'%(err) 

        if output:
            print ' OUT:\n%s'%(out) 
            if err!='':
                print '\n ERR:\n%s'%(err) 

        return

    #-----------------------------------------------------------------------------------------------
    # find number of all jobs on this scheduler
    #-----------------------------------------------------------------------------------------------
    def findNumberOfTotalJobs(self):

        cmd = 'condor_q | grep running| cut -d\' \' -f1  2> /dev/null'
        if not self.isLocal():
            cmd = 'ssh -x ' + self.user + '@' + self.host + ' \"' + cmd + '\"'

        nJobs = 1000000
        if DEBUG > 0:
            print " CMD " + cmd
        for line in os.popen(cmd).readlines():  # run command
            nJobs = int(line[:-1])

        cmd = 'condor_q ' + self.user + '| grep running| cut -d\' \' -f1  2> /dev/null'
        if not self.isLocal():
            cmd = 'ssh -x ' + self.user + '@' + self.host + ' \"' + cmd + '\"'

        nMyJobs = 1000000
        for line in os.popen(cmd).readlines():  # run command
            nMyJobs = int(line[:-1])

        return (nJobs,nMyJobs)

    #-----------------------------------------------------------------------------------------------
    # find the home directory where we submit
    #-----------------------------------------------------------------------------------------------
    def findHome(self,host,user):

        cmd = 'ssh ' + user + '@' + host + ' pwd'
        home = ''
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            home = line

        return home

    #-----------------------------------------------------------------------------------------------
    # find the user id where we submit
    #-----------------------------------------------------------------------------------------------
    def findRemoteUid(self,host,user):

        cmd = 'ssh ' + user + '@' + host + ' id -u'
        ruid = ''
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            ruid = line

        return ruid

    #-----------------------------------------------------------------------------------------------
    # find local proxy path
    #-----------------------------------------------------------------------------------------------
    def findLocalProxy(self):

        localProxy = ""
        cmd = 'voms-proxy-info -path'
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            localProxy = line

        return localProxy

    #-----------------------------------------------------------------------------------------------
    # Is the scheduler local?
    #-----------------------------------------------------------------------------------------------
    def isLocal(self):

        return (self.host == self.here)

    #-----------------------------------------------------------------------------------------------
    # push local proxy to remote location
    #-----------------------------------------------------------------------------------------------
    def pushProxyToScheduler(self):

        if self.isLocal():
            pass
        else:
            localProxy = self.findLocalProxy()
            remoteProxy = "/tmp/x509up_u" + self.ruid
            cmd = "scp -q " + localProxy + " " + self.user + '@' +  self.host + ':' + remoteProxy
            os.system(cmd)

        return

    #-----------------------------------------------------------------------------------------------
    # show the scheduler parameters
    #-----------------------------------------------------------------------------------------------
    def show(self):

        print ' ====  S c h e d u l e r  ===='
        print ' Here: ' + self.here
        print ' Host: ' + self.host
        print ' User: ' + self.user
        print ' Base: ' + self.base

    #-----------------------------------------------------------------------------------------------
    # update on the fly
    #-----------------------------------------------------------------------------------------------
    def update(self,host='submit.mit.edu',user='cmsprod',base=''):

        self.host = host
        self.user = user

        if base == '':
            self.base = self.findHome(host,user)
        else:
            self.base = base
        self.ruid = self.findRemoteUid(host,user)
        (self.nTotal,self.nMyTotal) = self.findNumberOfTotalJobs()

        self.pushProxyToScheduler()

        return

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

        # fill contents
        self.loadAllLfns(self.makeLfnFile())
        self.loadAllJobs(self.makeJobFile())
        self.loadSites(self.makeSiteFile())

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

        if file not in self.allJobs.keys():
            print ' ERROR -- found completed job not in list of all jobs?! ->' + file + '<-'
        if file in self.completedJobs.keys():
            print " ERROR -- completed job appeared twice! Should not happen. EXIT (%s)"%file
            sys.exit(1)
        # add this job to the mix
        self.completedJobs[file] = self.allJobs[file]

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

#---------------------------------------------------------------------------------------------------
"""
Class:  Task(tag,config,version,cmssw,dataset,dbs,jobFile,siteFile)
Each task in condor can be described through this class
"""
#---------------------------------------------------------------------------------------------------
class Task:
    "Description of a Task in condor"

    #-----------------------------------------------------------------------------------------------
    # constructor for new creation
    #-----------------------------------------------------------------------------------------------
    def __init__(self,tag,request):


        # from the call
        self.tag = tag
        self.request = request

        # create some shortcuts
        self.scheduler = self.request.scheduler
        self.sample = self.request.sample

        # derived
        self.cmsswVersion = self.findCmsswVersion()
        self.nJobs = 0
        self.submitCmd = 'submit_' +  self.tag + '.cmd'
        self.logs = self.scheduler.base + '/cms/logs/' + self.request.config + '/' \
            + self.request.version + '/' + self.sample.dataset
        self.outputData = self.scheduler.base + '/cms/data/' + self.request.config + '/' \
            + self.request.version + '/' + self.sample.dataset
        self.tarBall = self.logs + '/kraken_' + self.cmsswVersion + '.tgz'
        self.executable = self.logs + '/' + os.getenv('KRAKEN_SCRIPT')
        self.lfnFile = self.logs + '/' + self.sample.dataset + '.lfns'

        # show what we got
        print ''
        self.show()
        print ''

    #-----------------------------------------------------------------------------------------------
    # add specification to given file for exactly one more condor queue request (one job)
    #-----------------------------------------------------------------------------------------------
    def addJob(self,fileH,file,job):

        gpack = file.replace('.root','')

        fileH.write("Arguments = " + os.getenv('KRAKEN_EXE') + ' ' + self.request.config + ' ' \
                        + self.request.version + ' ' + ' ' + self.request.py + ' ' \
                        + self.sample.dataset + ' ' + gpack + ' ' + job + ' ' + self.tag + '\n')
        fileH.write("Output = " + self.logs + '/' + gpack + '.out' + '\n')
        fileH.write("Error = " + self.logs + '/' + gpack + '.err' + '\n')
        fileH.write("transfer_output_files = " + gpack + '.empty' + '\n')
        fileH.write("Queue" + '\n')

    #-----------------------------------------------------------------------------------------------
    # remove remainders from submission
    #-----------------------------------------------------------------------------------------------
    def cleanUp(self):

        # log and output data dirs
        print " INFO - removing submit script "
        os.system("rm -rf " + self.submitCmd)

    #-----------------------------------------------------------------------------------------------
    # submit condor job
    #-----------------------------------------------------------------------------------------------
    def condorSubmit(self):

        # make sure this condorTask has jobs to be submitted
        if self.nJobs<1 or self.scheduler.nMyTotal > 20000 or self.scheduler.nTotal > 100000:
            print ' NO SUBMISSION: %d (nJobs)  %d (nMyTotal)  %d (nTotal)\n'\
                %(self.nJobs,self.scheduler.nMyTotal,self.scheduler.nTotal)
            return

        # start with the base submit script
        cmd = 'condor_submit ' +  self.submitCmd
        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
                + ' \"cd ' + self.logs + '; ' + cmd + '\"'
        os.system(cmd)

    #-----------------------------------------------------------------------------------------------
    # create the required local and remote directories
    #-----------------------------------------------------------------------------------------------
    def createDirectories(self):

        # log and output data dirs
        print " INFO - make local directories "
        cmd = "mkdir -p " + self.logs + " " + self.outputData
        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host + ' ' + cmd
        os.system(cmd)

        # remote directories for kraken output
        print " INFO - make remote directories "
        cmd = "makedir --p " + self.request.base + "/" + self.request.config + '/' \
                      + self.request.version + '/' + self.sample.dataset + '/' + self.tag
        #print " MKDIR: " + cmd
        os.system(cmd)
        cmd = "changemod --options=a+rwx " + self.request.base + "/" \
                      + self.request.config + '/' + self.request.version + '/' \
                      + self.sample.dataset + '/' + self.tag
        #print " CHMOD: " + cmd
        os.system(cmd)


    #-----------------------------------------------------------------------------------------------
    # find the present CMSSW version
    #-----------------------------------------------------------------------------------------------
    def findCmsswVersion(self):
        cmd = "ls -1rt %s/%s/"%(os.getenv('KRAKEN_CMSSW'),self.request.version)
        print " CMD: " + cmd
        myRex = rex.Rex()
        (rc,out,err) = myRex.executeLocalAction(cmd)
        cmsswVersion = ""
        for line in out.split("\n"):
            if 'CMSSW_' in line:
                cmsswVersion = line
        print " CMSSW: " + cmsswVersion
    
        return (cmsswVersion.replace('CMSSW_',''))

    #-----------------------------------------------------------------------------------------------
    # generate actual tarball, or leave as is if already up to date
    #-----------------------------------------------------------------------------------------------
    def makeTarBall(self):

        cmsswBase = "%s/%s/CMSSW_%s"%\
            (os.getenv('KRAKEN_CMSSW'),self.request.version,self.cmsswVersion)

        # check if the tar ball exists locally
        if os.path.exists(cmsswBase + "/kraken_" + self.cmsswVersion + ".tgz"):
            print " INFO - tar ball exists: " \
                + cmsswBase + "/kraken_" + self.cmsswVersion + ".tgz"
        else:
            print ' Make kraken tar ball: ' \
                + cmsswBase + "/kraken_" + self.cmsswVersion + ".tgz"
            cmd = "cd " + cmsswBase \
                + "; tar fch kraken_" + self.cmsswVersion + ".tar bin/ lib/ src/"
            #print ' CMD: ' + cmd
            os.system(cmd)
            cmd = "cd " + cmsswBase \
                + "; tar fr kraken_" + self.cmsswVersion + ".tar  python/"
            #print ' CMD: ' + cmd
            os.system(cmd)
            cmd = "cd " + os.getenv('KRAKEN_BASE') \
                + "; tar fr " + cmsswBase + "/kraken_" + self.cmsswVersion + ".tar tgz/ " \
                + self.request.config + "/" + self.request.version
            #print ' CMD: ' + cmd
            os.system(cmd)
            cmd = "cd " + cmsswBase \
                + "; gzip kraken_" + self.cmsswVersion + ".tar; mv  kraken_" \
                + self.cmsswVersion + ".tar.gz  kraken_"  + self.cmsswVersion + ".tgz"
            #print ' CMD: ' + cmd
            os.system(cmd)

        # see whether the tar ball needs to be copied locally or to remote scheduler
        if self.scheduler.isLocal():
            cmd = "cp " + cmsswBase+ "/kraken_" + self.cmsswVersion + ".tgz " \
                + self.logs
            os.system(cmd)
            # also copy the script over
            cmd = "cp " + os.getenv('KRAKEN_BASE') + "/bin/" + os.getenv('KRAKEN_SCRIPT') + " " \
                + self.logs
            os.system(cmd)
            # also copy the lfn list over 
            cmd = "cp " + os.getenv('KRAKEN_WORK') + '/lfns/' + self.sample.dataset + '.lfns' \
                + " " + self.logs
            os.system(cmd)
        else:
            cmd = "scp -q " + cmsswBase + "/kraken_" + self.cmsswVersion + ".tgz " \
                + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)
            cmd = "scp -q " + os.getenv('KRAKEN_BASE') + "/bin/" + os.getenv('KRAKEN_SCRIPT') \
                + " " + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)
            cmd = "scp -q " + os.getenv('KRAKEN_WORK') + '/lfns/' + self.sample.dataset + '.lfns' \
                + " " + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)

        return

    #-----------------------------------------------------------------------------------------------
    # present the current condor task
    #-----------------------------------------------------------------------------------------------
    def show(self):

        print ' ==== C o n d o r  T a s k  I n f o r m a t i o n  ===='
        print ' '
        print ' Tag     : ' + self.tag
        print ' Base    : ' + self.request.base
        print ' Config  : ' + self.request.config
        print ' Version : ' + self.request.version
        print ' CMSSW py: ' + self.request.py
        print ' '
        self.sample.show()
        print ' '
        self.scheduler.show()

    #-----------------------------------------------------------------------------------------------
    # write condor submission configuration
    #-----------------------------------------------------------------------------------------------
    def writeCondorSubmit(self):

        # make sure to keep track of the number of jobs created
        self.nJobs = 0

        # start with the base submit script
        cmd = 'cat ' + os.getenv('KRAKEN_BASE') + '/condor/req-all.sub ' \
            +          os.getenv('KRAKEN_BASE') + '/condor/base.sub > ' \
            +  self.submitCmd
        os.system(cmd)

        # attach the additional processing lines defining the specifc JOB productions
        with open(self.submitCmd,'a') as fileH:
            fileH.write("Environment = \"HOSTNAME=" + os.getenv('HOSTNAME') + \
                            "; KRAKEN_EXE=" + os.getenv('KRAKEN_EXE') + "\"" + '\n')
            fileH.write("Initialdir = " + self.outputData + '\n')
            fileH.write("Executable = " + self.executable + '\n')
            fileH.write("Log = " + self.logs + '/' + self.sample.dataset + '.log' + '\n')
            fileH.write("transfer_input_files = " + self.tarBall + ',' + self.lfnFile + '\n')

            for file,job in self.sample.missingJobs.iteritems():
                print ' Adding : %s %s'%(file,job)
                self.nJobs += 1
                self.addJob(fileH,file,job)

        # make sure submit script is in the right place
        if not self.scheduler.isLocal() and self.nJobs>0:
            cmd = "scp -q " + self.submitCmd + " " \
                + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)
            cmd = "ssh -x " + self.scheduler.user + '@' +  self.scheduler.host \
                + ' \"voms-proxy-info -exists || voms-proxy-init --valid 168:00 -voms cms >& /dev/null\" '
            os.system(cmd)

#---------------------------------------------------------------------------------------------------
"""
Class:  TaskCleaner(condorTask)

A given condor task can be cleaned with this tool.

Method to remove all log files of successfully completed jobs and analysis of all failed jobs and
remove the remaining condor queue entires of the held jobs.

We are assuming that any failed job is converted into a held job. We collect all held jobs from the
condor queue and safe those log files into our web repository for browsing. Only the last copy of
the failed job is kept as repeated failure overwrites the old failed job's log files. The held job
entries in the condor queue are removed on the failed job is resubmitted.

It should be noted that if a job succeeds all log files including the ones from earlier failures
will be removed.

"""
#---------------------------------------------------------------------------------------------------
class TaskCleaner:

    "The cleaner of a given condor task."

    #-----------------------------------------------------------------------------------------------
    # constructor for new creation
    #-----------------------------------------------------------------------------------------------
    def __init__(self,task):

        self.task = task
        self.localUser = os.getenv('USER')

        self.logRemoveScript = ''  # '#!/bin/bash\n'
        self.webRemoveScript = ''  # '#!/bin/bash\n'
        self.logSaveScript = ''    # '#!/bin/bash\n'

        self.rex = rex.Rex(self.task.scheduler.host,self.task.scheduler.user)

    #-----------------------------------------------------------------------------------------------
    # analyze known failures
    #-----------------------------------------------------------------------------------------------
    def logCleanup(self):
        #

        print '\n ====  C l e a n e r  ===='

        # A - take all completed jobs and remove all related logs
        self.removeCompletedLogs()

        # B - find all logs from the held jobs, save them and generate failure summary
        self.saveFailedLogs()
        self.analyzeLogs()

        # C - remove all held jobs from the queue
        self.removeHeldJobs()

        return

    #-----------------------------------------------------------------------------------------------
    # analyze saved logs and produce a summary web page
    #-----------------------------------------------------------------------------------------------
    def analyzeLogs(self):

        cfg = self.task.request.config
        vers = self.task.request.version
        dset = self.task.request.sample.dataset

        local = os.getenv('KRAKEN_AGENTS_LOG') + '/reviewd/%s/%s/%s/README'%(cfg,vers,dset)

        print ' - analyze failed logs'
        cmd = "analyzeErrors.py --config=%s --version=%s --dataset=%s >& %s"%(cfg,vers,dset,local)
        (rc,out,err) = self.rex.executeLocalAction(cmd)
        
        return

    #-----------------------------------------------------------------------------------------------
    # remove all log files of completed jobs
    #-----------------------------------------------------------------------------------------------
    def removeCompletedLogs(self):

        cfg = self.task.request.config
        vers = self.task.request.version
        dset = self.task.request.sample.dataset

        local = os.getenv('KRAKEN_AGENTS_LOG') + '/reviewd'

        print ' - remove completed logs'

        for file,job in self.task.sample.completedJobs.iteritems():
            # we will make a lot of reference to the ID
            id = file.replace('.root','')

            cmd = 'rm -f cms/*/%s/%s/%s/*%s*\n'%(cfg,vers,dset,id)
            self.logRemoveScript += cmd

            cmd = 'rm -f %s/%s/%s/%s/*%s*\n'%(local,cfg,vers,dset,id)
            self.webRemoveScript += cmd

        for file,job in self.task.sample.noCatalogJobs.iteritems():
            # we will make a lot of reference to the ID
            id = file.replace('.root','')

            cmd = 'rm cms/*/%s/%s/%s/*%s* 2> /dev/null\n'%(cfg,vers,dset,id)
            self.logRemoveScript += cmd

            cmd = 'rm -f %s/%s/%s/%s/*%s*\n'%(local,cfg,vers,dset,id)
            self.webRemoveScript += cmd

        print ' -- LogRemoval'
        (irc,rc,out,err) = self.rex.executeLongAction(self.logRemoveScript)
        print ' -- WebRemoval'
        (rc,out,err) = self.rex.executeLocalLongAction(self.webRemoveScript)

        return

    #-----------------------------------------------------------------------------------------------
    # remove held jobs from the queue
    #-----------------------------------------------------------------------------------------------
    def removeHeldJobs(self):

        base = self.task.scheduler.base + "/cms/data"
        iwd = base + "/%s/%s/%s"%\
            (self.task.request.config,self.task.request.version,self.task.request.sample.dataset)
        cmd = 'condor_rm -constraint "JobStatus==5 && Iwd==\\\"%s\\\""'%(iwd)
        irc = 0
        rc = 0

        print ' - remove Held jobs (there are %d): %s'%(len(self.task.request.sample.heldJobs),cmd)
        if not self.task.scheduler.isLocal():
            (irc,rc,out,err) = self.rex.executeAction(cmd)
            if DEBUG > 0 and (irc != 0 or rc != 0):
                print ' IRC: %d'%(irc) 
        else:
            (rc,out,err) = self.rex.executeLocalAction(cmd)
            
        if DEBUG > 0 and (irc != 0 or rc != 0):
            print ' RC: %d'%(rc) 
            print ' ERR:\n%s'%(err) 
            print ' OUT:\n%s'%(out) 

        return

    #-----------------------------------------------------------------------------------------------
    # save the log files of the failed jobs
    #-----------------------------------------------------------------------------------------------
    def saveFailedLogs(self):

        cfg = self.task.request.config
        vers = self.task.request.version
        dset = self.task.request.sample.dataset

        local = os.getenv('KRAKEN_AGENTS_LOG') + '/reviewd'

        print ' - find failed logs'

        # make the directory in any case
        cmd = 'mkdir -p %s/%s/%s/%s/;'%(local,cfg,vers,dset)
        if DEBUG>0:
            print ' Mkdir: ' + cmd
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        # copy the indexer to make it pretty
        cmd = 'cp ' + os.getenv('KRAKEN_AGENTS_BASE') + '/html/index-sample.php ' \
            + '%s/%s/%s/%s/index.php'%(local,cfg,vers,dset)
        if DEBUG>0:
            print ' index: ' + cmd
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        # construct the script to make the tar ball
        self.logSaveScript += 'cd cms/logs/%s/%s/%s\ntar fzc %s-%s-%s.tgz'\
            %(cfg,vers,dset,cfg,vers,dset)

        # find out whether we have held jobs == failures
        haveFailures = False
        for file,job in self.task.sample.heldJobs.iteritems():
            id = file.replace('.root','')
            cmd = '  \\\n  %s.{out,err}'%(id)
            self.logSaveScript += cmd
            haveFailures = True

        # no need to continue if there are no failures
        if not haveFailures:
            print ' INFO - no failed jobs found.'
            return

        # log saver script
        print self.logSaveScript
        (irc,rc,out,err) = self.rex.executeLongAction(self.logSaveScript)

        # pull the tar ball over
        cmd = 'scp ' + self.task.scheduler.user + '@' + self.task.scheduler.host \
            + ':cms/logs/%s/%s/%s/%s-%s-%s.tgz'%(cfg,vers,dset,cfg,vers,dset) \
            + ' %s/%s/%s/%s/'%(local,cfg,vers,dset)
        if DEBUG>0:
            print ' Get tar: ' + cmd
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        cmd = 'cd %s/%s/%s/%s/\n'%(local,cfg,vers,dset) \
            + 'tar fzx %s-%s-%s.tgz\n'%(cfg,vers,dset) \
            + 'chmod a+r *'
        if DEBUG>0:
            print ' Untar: ' + cmd
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        cmd = 'rm -f %s/%s/%s/%s/%s-%s-%s.tgz'%(local,cfg,vers,dset,cfg,vers,dset) 
        if DEBUG>0:
            print ' Remove local tar: ' + cmd
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        cmd = 'rm -f cms/logs/%s/%s/%s/%s-%s-%s.tgz'%(cfg,vers,dset,cfg,vers,dset)
        if DEBUG>0:
            print ' Remove remote tar: ' + cmd
        (irc,rc,out,err) = self.rex.executeAction(cmd)

        return
