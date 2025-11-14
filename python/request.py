#---------------------------------------------------------------------------------------------------
# Python Module File to describe processing request
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import os
import random
from scheduler import Scheduler
from sample import Sample

DEBUG = 0

#---------------------------------------------------------------------------------------------------
"""
Class:  Request(scheduler=None,sample=None,config='filefi',version='046',py='data')
A request will have to specify the configuration, version and python configuration file to be
applied to the also given scheduler and sample.
"""
#---------------------------------------------------------------------------------------------------
class Request:
    "Description of a request for a specific sample processing."

    #-----------------------------------------------------------------------------------------------
    # constructor
    #-----------------------------------------------------------------------------------------------
    def __init__(self,schedulers=None,sample=None,config='filefi',version='046',py='data'):
        
        self.base = os.getenv('KRAKEN_SE_BASE')

        self.scheduler = None
        self.owner = None
        self.sample = sample
        self.config = config
        self.version = version
        self.py = py

        self.establishState()

        # settle the owner of this request
        if not self.owner:
            # get random sheduler
            self.owner = random.choice(list(schedulers.keys()))
        # get the corresponding scheduler
        self.scheduler = schedulers[self.owner]
        print(f" Request owner is: {self.owner}")
            
    #-----------------------------------------------------------------------------------------------
    # establish the full state of the request (this resets existing info)
    #-----------------------------------------------------------------------------------------------
    def establishState(self):
        print(" -- Establish request status --")
        # talk to condor
        self.loadQueuedJobs()
        self.loadHeldJobs()
        # check the file outputs
        self.loadCompletedJobs()
        # check how often this job was tried already
        self.loadNFailedJobs()
        # make a list of all missing jobs
        self.sample.createMissingJobs()
        return
        
    #-----------------------------------------------------------------------------------------------
    # load all jobs so far completed relevant to this task
    #-----------------------------------------------------------------------------------------------
    def show(self):
        print(" Missing or failed jobs ")
        self.sample
        
    #-----------------------------------------------------------------------------------------------
    # load all jobs so far completed relevant to this task
    #-----------------------------------------------------------------------------------------------
    def loadCompletedJobs(self):

        # initialize from scratch
        self.sample.resetCompletedJobs()
        self.sample.resetNoCatalogJobs()
        
        # initialize from scratch
        path = f"{self.base}/{self.config}/{self.version}/{self.sample.dataset}"
        # first fully checked files
        cmd = 'list ' + path + '  2> /dev/null | grep root'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split()
            file = (f[1].split("/")).pop()
            self.sample.addCompletedJob(file)
        # now also look at the temporary files (not yet cataloged)
        cmd = 'list ' + path + '/' + os.getenv('KRAKEN_TMP_PREFIX') \
            + '*/  2> /dev/null | grep _tmp.root'
        for line in os.popen(cmd).readlines():  # run command
            f    = line.split()
            file = (f[1].split("/")).pop()
            file = file.replace('_tmp','')
            self.sample.addNoCatalogJob(file)
        if DEBUG > 0:
            print(' NOCATAL - Jobs: %6d'%(len(self.sample.noCatalogJobs)))
            print(' DONE    - Jobs: %6d'%(len(self.sample.completedJobs)))

    #-----------------------------------------------------------------------------------------------
    # load all jobs that are presently queued
    #-----------------------------------------------------------------------------------------------
    def loadQueuedJobs(self):

        # initialize from scratch
        self.sample.resetQueuedJobs()

        script = os.getenv('KRAKEN_SCRIPT')
        path = f"{self.base}/{self.config}/{self.version}/{self.sample.dataset}"
        pattern = f"{self.config} {self.version} {self.py} {self.sample.dataset}"
        cmd = f'condor_q -all -constraint \'regexp(\"{script}\", Cmd) && JobStatus!=5\' -format \'%s \' Owner -format \'%s\n\' Args 2> /dev/null|grep \'{pattern}\''

        # you cannot look at the queue when the scheduler is not set ...
        #if not self.scheduler.isLocal():
        #    cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
        #        + ' \"' + cmd + '\"'

        for line in os.popen(cmd).readlines():  # run command
            #print(f" loadQueuedJobs {line}")
            f    = line.split(' ')
            self.owner = f[0]
            file = f[6] + '.root'
            self.sample.addQueuedJob(file)
        if DEBUG > 0:
            print(' QUEUED  - Jobs: %6d'%(len(self.sample.queuedJobs)))

    #-----------------------------------------------------------------------------------------------
    # load all jobs that are presently queued but in held state
    #-----------------------------------------------------------------------------------------------
    def loadHeldJobs(self):

        # initialize from scratch
        self.sample.resetHeldJobs()

        path = self.base + '/' + self.config + '/' + self.version + '/' \
            + self.sample.dataset
        pattern = "%s %s %s %s"%(self.config,self.version,self.py,self.sample.dataset)

        script = os.getenv('KRAKEN_SCRIPT')
        cmd = f'condor_q -all -constraint \'regexp(\"{script}\", Cmd) && JobStatus==5\' -format \'%s \' Owner -format \'%s\n\' Args 2> /dev/null|grep \'{pattern}\''
        # you cannot look at the queue when the scheduler is not set ...
        #if not self.scheduler.isLocal():
        #    cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
        #        + ' \"' + cmd + '\"'
        for line in os.popen(cmd).readlines():  # run command
            #print(f" loadHeldJobs {line}")
            f    = line.split(' ')
            file = f[6] + '.root'
            self.sample.addHeldJob(file)

        if DEBUG > 0:
            print(' HELD    - Jobs: %6d'%(len(self.sample.heldJobs)))

    #-----------------------------------------------------------------------------------------------
    # load the number of failures each job had so far
    #-----------------------------------------------------------------------------------------------
    def loadNFailedJobs(self):

        # initialize from scratch
        self.sample.resetNFailedJobs()
       
        trunc = "%s/reviewd"%(os.getenv('KRAKEN_AGENTS_WWW'))
        file_name = "%s/%s/%s/%s/ncounts.err"%(trunc,self.config,self.version,self.sample.dataset)

        # read all data
        data = ''
        if os.path.exists(file_name):
            with open(file_name,"r") as file:
                data = file.read()

        # make a list from the data
        for row in data.split("\n"):
            if len(row) < 2:
                continue
            file = row.split(' ')[0]
            n = int(row.split(' ')[1])
            self.sample.addNFailedJob(file,n)
