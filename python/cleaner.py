#---------------------------------------------------------------------------------------------------
# Python Module File to describe a cleaner
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import os,sys,re,string,socket
import rex
from task import Task

DEBUG = 0

#---------------------------------------------------------------------------------------------------
"""Class:  Cleaner(condorTask)

A given condor task can be cleaned with this tool.

Method to remove all log files of successfully completed jobs and analysis of all failed jobs and
remove the remaining condor queue entires of the held jobs.

We are assuming that most failed jobs are converted into a held jobs but also consider jobs that are
not otherwise completed to be 'failed' jobs. We collect all failed jobs and safe those log files
into our web repository for browsing. Only the last copy of the failed job is kept as repeated
failure overwrites the old failed job's log files. The held job entries in the condor queue are
removed and all failed job are resubmitted.

It should be noted that if a job succeeds all log files including the ones from earlier failures
will be removed.

"""
#---------------------------------------------------------------------------------------------------
class Cleaner:

    "The cleaner of a given condor task."

    #-----------------------------------------------------------------------------------------------
    # constructor for new creation
    #-----------------------------------------------------------------------------------------------
    def __init__(self,task):

        self.task = task
        self.localUser = os.getenv('USER')

        self.activity = os.getenv('KRAKEN_ACTIVITY')

        self.logRemoveScript = ''
        self.webRemoveScript = ''
        self.logSaveScript = ''

        self.rex = rex.Rex(self.task.scheduler.host,self.task.scheduler.user)

    #-----------------------------------------------------------------------------------------------
    # kill all queued jobs (running, idle, held etc.)
    #-----------------------------------------------------------------------------------------------
    def killQueued(self):

        print('\n ====  C l e a n e r -- kill queue ====')

        # run condor command to kill all queued jobs from this task
        self.removeAllJobs()

        # regenerate the request status
        self.task.request.establishState()
        
        return

    #-----------------------------------------------------------------------------------------------
    # analyze known failures
    #-----------------------------------------------------------------------------------------------
    def logCleanup(self):

        print('\n ====  C l e a n e r  ====')

        # A - take all completed jobs and remove all related logs
        self.removeCompletedLogs()

        # B - find all logs from the held and quietly failed jobs, save and generate summary
        self.saveFailedLogs()
        self.analyzeLogs()

        # C - remove all held jobs from the queue
        self.removeHeldJobs()

        # D - remove entire cache on scheduler (if dataset completed)
        self.removeCache()

        # E - other leftover directory stubs
        self.removeDirectoryStubs()

        return

    #-----------------------------------------------------------------------------------------------
    # analyze saved logs and produce a summary web page
    #-----------------------------------------------------------------------------------------------
    def analyzeLogs(self):

        cfg = self.task.request.config
        vers = self.task.request.version
        dset = self.task.request.sample.dataset

        local = os.getenv('KRAKEN_AGENTS_LOG') + '/reviewd/%s/%s/%s/README'%(cfg,vers,dset)

        print(' - analyze failed logs')
        cmd = "failedFiles.py --book=%s/%s --pattern=%s"%(cfg,vers,dset)
        if DEBUG > 0:
            print("   CMD: %s"%(cmd))
        (rc,out,err) = self.rex.executeLocalAction(cmd)
        #print(out)

        # make sure to reload this
        self.task.request.loadNFailedJobs()

        cmd = "analyzeErrors.py --config=%s --version=%s --dataset=%s >& %s"%(cfg,vers,dset,local)
        if DEBUG > 0:
            print("   CMD: %s"%(cmd))
        (rc,out,err) = self.rex.executeLocalAction(cmd)
        
        return

    #-----------------------------------------------------------------------------------------------
    # remove all log files of completed jobs or queued
    #-----------------------------------------------------------------------------------------------
    def removeCompletedLogs(self):

        cfg = self.task.request.config
        vers = self.task.request.version
        dset = self.task.request.sample.dataset

        local = os.getenv('KRAKEN_AGENTS_LOG') + '/reviewd'

        print(' - remove completed logs')

        #print(' -->>> SKIPPING')
        #return
        
        #for file,job in self.task.sample.completedJobs.iteritems():
        for (file,job) in self.task.sample.completedJobs.items():
            # we will make a lot of reference to the ID
            id = file.replace('.root','')

            cmd = 'rm -f %s/*/%s/%s/%s/*%s*\n'%(self.activity,cfg,vers,dset,id)
            self.logRemoveScript += cmd

            cmd = 'rm -f %s/%s/%s/%s/*%s*\n'%(local,cfg,vers,dset,id)
            self.webRemoveScript += cmd

        for (file,job) in self.task.sample.noCatalogJobs.items():
            # we will make a lot of reference to the ID
            id = file.replace('.root','')

            cmd = 'rm -f %s/*/%s/%s/%s/*%s*\n'%(self.activity,cfg,vers,dset,id)
            self.logRemoveScript += cmd

            cmd = 'rm -f %s/%s/%s/%s/*%s*\n'%(local,cfg,vers,dset,id)
            self.webRemoveScript += cmd

        for (file,job) in self.task.sample.queuedJobs.items():
            # we will make a lot of reference to the ID
            id = file.replace('.root','')

            cmd = 'rm -f %s/*/%s/%s/%s/*%s*\n'%(self.activity,cfg,vers,dset,id)
            self.logRemoveScript += cmd

            cmd = 'rm -f %s/%s/%s/%s/*%s*\n'%(local,cfg,vers,dset,id)
            self.webRemoveScript += cmd

        print(' -- LogRemoval')
        (irc,rc,out,err) = self.rex.executeLongAction(self.logRemoveScript)
        print(' -- WebRemoval')
        (rc,out,err) = self.rex.executeLocalLongAction(self.webRemoveScript)

        return

    #-----------------------------------------------------------------------------------------------
    # remove entire remote cache of this task
    #-----------------------------------------------------------------------------------------------
    def removeCache(self):

        print(' - trying to remove task cache')

        if len(self.task.sample.completedJobs) == len(self.task.sample.allJobs):
            print('   job is complete, remove the potentially remaining cache.')
        else:
            return

        cmd = "rm -rf " + self.task.logs
        if DEBUG > 0:
            print("   CMD: %s"%(cmd))
        
        if self.task.scheduler.isLocal():
            (rc,out,err) = self.rex.executeLocalAction(cmd)
        else:
            (irc,rc,out,err) = self.rex.executeAction(cmd)
            if DEBUG > 0 and (irc != 0 or rc != 0):
                print(' IRC: %d'%(irc))
            
        if DEBUG > 0 and (irc != 0 or rc != 0):
            print(' RC: %d'%(rc))
            print(' ERR:\n%s'%(err))
            print(' OUT:\n%s'%(out))

        return

    #-----------------------------------------------------------------------------------------------
    # remove entire remote cache of this task
    #-----------------------------------------------------------------------------------------------
    def removeDirectoryStubs(self):

        print(' - trying to remove remaining directory stubs in storage')

        if len(self.task.sample.completedJobs) == len(self.task.sample.allJobs):
            print('   job is complete, remove the potentially remaining cache.')
        else:
            return

        cfg = self.task.request.config
        vers = self.task.request.version
        dset = self.task.request.sample.dataset

        prefix = os.getenv('KRAKEN_TMP_PREFIX')
        base = os.getenv('KRAKEN_SE_BASE')

        directory = '%s/%s/%s/%s/%s*'%(base,cfg,vers,dset,prefix)

        cmd = " removedir " + directory
        if DEBUG > 0:
            print("   CMD: %s"%(cmd))

        (rc,out,err) = self.rex.executeLocalAction(cmd)

        if DEBUG > 0 and rc != 0:
            print(' RC: %d'%(rc))
            print(' ERR:\n%s'%(err))
            print(' OUT:\n%s'%(out))

        return

    #-----------------------------------------------------------------------------------------------
    # remove all jobs from the queue
    #-----------------------------------------------------------------------------------------------
    def removeAllJobs(self):

        base = self.task.scheduler.base + "/%s/data"%self.activity
        iwd = base + "/%s/%s/%s"%\
            (self.task.request.config,self.task.request.version,self.task.request.sample.dataset)
        cmd = 'condor_rm -constraint "Iwd==\\\"%s\\\""'%(iwd)
        irc = 0
        rc = 0

        print(' - remove all jobs: %s'%(cmd))
        if not self.task.scheduler.isLocal():
            (irc,rc,out,err) = self.rex.executeAction(cmd)
            if DEBUG > 0 and (irc != 0 or rc != 0):
                print(' IRC: %d'%(irc))
        else:
            (rc,out,err) = self.rex.executeLocalAction(cmd)
            
        if DEBUG > 0 and (irc != 0 or rc != 0):
            print(' RC: %d'%(rc))
            print(' ERR:\n%s'%(err))
            print(' OUT:\n%s'%(out))

        return
    
    #-----------------------------------------------------------------------------------------------
    # remove held jobs from the queue
    #-----------------------------------------------------------------------------------------------
    def removeHeldJobs(self):

        base = self.task.scheduler.base + "/%s/data"%self.activity
        iwd = base + "/%s/%s/%s"%\
            (self.task.request.config,self.task.request.version,self.task.request.sample.dataset)
        cmd = 'condor_rm -constraint "JobStatus==5 && Iwd==\\\"%s\\\""'%(iwd)
        irc = 0
        rc = 0

        if len(self.task.request.sample.heldJobs) > 0:
            print(' - remove held jobs (n=%d): %s'%(len(self.task.request.sample.heldJobs),cmd))
            if not self.task.scheduler.isLocal():
                (irc,rc,out,err) = self.rex.executeAction(cmd)
                if DEBUG > 0 and (irc != 0 or rc != 0):
                    print(' IRC: %d'%(irc))
            else:
                (rc,out,err) = self.rex.executeLocalAction(cmd)
                
            if DEBUG > 0 and (irc != 0 or rc != 0):
                print(' RC: %d'%(rc))
                print(' ERR:\n%s'%(err))
                print(' OUT:\n%s'%(out))
        else:
            print(' - no held jobs to remove')

        return

    #-----------------------------------------------------------------------------------------------
    # save the log files of the failed jobs
    #-----------------------------------------------------------------------------------------------
    def saveFailedLogs(self):

        print(' - find failed logs')

        #print(' -->>> SKIPPING')
        #return

        # make sure this is not a new workflow
        if (self.task.request.sample.isNew):
            print(" - savedFailedLogs: new workflow needs no logs saving.")
            return

        # shortcuts to relevant configuration
        cfg = self.task.request.config
        vers = self.task.request.version
        dset = self.task.request.sample.dataset
        local = os.getenv('KRAKEN_AGENTS_LOG') + '/reviewd'

        # make the directory in any case
        cmd = 'mkdir -p %s/%s/%s/%s/;'%(local,cfg,vers,dset)
        if DEBUG>0:
            print(' Mkdir: %s'%(cmd))
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        # copy the indexer to make it pretty
        cmd = 'cp ' + os.getenv('KRAKEN_AGENTS_BASE') + '/html/index-sample.php ' \
            + '%s/%s/%s/%s/index.php'%(local,cfg,vers,dset)
        if DEBUG>0:
            print(' Index: %s'%(cmd))
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        # construct the script to make the tar ball
        self.logSaveScript += 'cd %s/logs/%s/%s/%s \n pwd \n tar --ignore-failed-read --create --gzip --file %s-%s-%s.tgz'\
            %(self.activity,cfg,vers,dset,cfg,vers,dset)

        # find out whether we have held jobs == failures
        haveFailures = False
        # OLD -- for file,job in self.task.sample.heldJobs.iteritems():
        for (file,job) in self.task.sample.missingJobs.items():
            id = file.replace('.root','')
            cmd = '  \\\n  %s.{out,err}'%(id)
            self.logSaveScript += cmd
            haveFailures = True

        # no need to continue if there are no failures
        if not haveFailures:
            if DEBUG>0:
                print(' INFO - no failed jobs found.')
            return

        # log saver script
        (irc,rc,out,err) = self.rex.executeLongAction(self.logSaveScript)
        if DEBUG>0:
            print(" CMD: %s\n IRC: %s RC: %s\n OUT: \n%s\n ERR: \n%s"%\
                  (self.logSaveScript,irc,rc,out,err))

        # pull the tar ball over
        cmd = 'scp ' + self.task.scheduler.user + '@' + self.task.scheduler.host \
            + ':%s/logs/%s/%s/%s/%s-%s-%s.tgz'%(self.activity,cfg,vers,dset,cfg,vers,dset) \
            + ' %s/%s/%s/%s/'%(local,cfg,vers,dset)
        if DEBUG>0:
            print(' Get tar: %s'%(cmd))
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        cmd = 'cd %s/%s/%s/%s/\n'%(local,cfg,vers,dset) \
            + 'tar fvzx %s-%s-%s.tgz\n'%(cfg,vers,dset) \
            + 'chmod a+r *'
        if DEBUG>0:
            print(' Untar: %s'%(cmd))
        (rc,out,err) = self.rex.executeLocalAction(cmd)

        cmd = 'rm -f %s/%s/%s/%s/%s-%s-%s.tgz'%(local,cfg,vers,dset,cfg,vers,dset) 
        if DEBUG>0:
            print(' Remove local tar: %s'%(cmd))
        (rc,out,err) = self.rex.executeLocalAction(cmd)
        
        cmd = 'rm -f %s/logs/%s/%s/%s/%s-%s-%s.tgz %s-%s-%s.tgz'%(self.activity,cfg,vers,dset,cfg,vers,dset,cfg,vers,dset)
        if DEBUG>0:
            print(' Remove remote tar: %s'%(cmd))
        (irc,rc,out,err) = self.rex.executeAction(cmd)
        if DEBUG>0:
            print(" CMD: %s\n IRC: %s RC: %s\n OUT: \n%s\n ERR: \n%s"%\
                  (cmd,irc,rc,out,err))

        return
