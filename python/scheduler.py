#---------------------------------------------------------------------------------------------------
# Python Module File to describe the scheduler
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import sys,os,socket
import rex

DEBUG = 0

#---------------------------------------------------------------------------------------------------
"""
Class:  Scheduler(host='submit05.mit.edu',user='paus')
Each sample can be described through this class
"""
#---------------------------------------------------------------------------------------------------
class Scheduler:
    "Description of a scheduler using condor"

    #-----------------------------------------------------------------------------------------------
    # constructor
    #-----------------------------------------------------------------------------------------------
    def __init__(self,host='submit05.mit.edu',user='paus',base='',nMyTotalMax=35000,nTotalMax=100000):

        self.here = socket.gethostname()
        self.host = host
        self.user = user
        self.ruid = 0
        self.base = base

        self.nMyTotalMax = nMyTotalMax
        self.nTotalMax = nTotalMax
        self.nTotal = 0
        self.nMyTotal = 0

        self.condorVersion = self.findCondorVersion()
        self.update(host,user,base,nMyTotalMax,nTotalMax)


    #-----------------------------------------------------------------------------------------------
    # execute a condor command on the given scheduler
    #-----------------------------------------------------------------------------------------------
    def executeCondorCmd(self,cmd='condor_q',output=False):

        if output:
            print(' execute condor command: %s'%(cmd))

        myRx = rex.Rex(self.host,self.user);
        irc = 0

        if not self.isLocal():
            (irc,rc,out,err) = myRx.executeAction(cmd)
            if (irc != 0 or rc != 0):
                print(' ERROR -- IRC: %d'%(irc))
        else:
            (rc,out,err) = myRx.executeLocalAction(cmd)
            
        if (irc != 0 or rc != 0):
            print(' ERROR -- RC: %d'%(rc))
            print(' ERROR -- ERR:\n%s'%(err))

        if output:
            print(' OUT:\n%s'%(out))
            if err!='':
                print('\n ERR:\n%s'%(err))

        return (rc,out,err)

    #-----------------------------------------------------------------------------------------------
    # find number of all jobs on this scheduler
    #-----------------------------------------------------------------------------------------------
    def findCondorVersion(self):
        cmd = 'condor_q -v|grep CondorVersion:|cut -d \' \' -f2|cut -d \'.\' -f1'
        if not self.isLocal():
            cmd = f'ssh -x {self.user}@{self.host} \" {cmd} \"'

        cv = -1
        for line in os.popen(cmd).readlines():  # run command
            cv = int(line[:-1])

        if DEBUG > 0:
            print(" Condor version: %d"%(self.condorVersion))

        return cv

    #-----------------------------------------------------------------------------------------------
    # find number of all jobs on this scheduler
    #-----------------------------------------------------------------------------------------------
    def findNumberOfTotalJobs(self):

        if self.condorVersion == 9:
            cmd = 'condor_q -all|grep running|cut -d\' \' -f13|tail -1  2> /dev/null'
        else:
            cmd = 'condor_q |grep running|cut -d\' \' -f13|tail -1  2> /dev/null'

        if not self.isLocal():
            cmd = f'ssh -x {self.user}@{self.host} \" {cmd} \"'

        nJobs = 1000000
        if DEBUG > 0:
            print(" CMD " + cmd)
        for line in os.popen(cmd).readlines():  # run command
            nJobs = int(line[:-1])

        if self.condorVersion == 9:
            cmd = f'condor_q {self.user}|grep running|grep query|cut -d\' \' -f12 2> /dev/null'
        else:
            cmd = f'condor_q {self.user} |grep running|cut -d\' \' -f11 2> /dev/null'

        if not self.isLocal():
            cmd = f'ssh -x {self.user}@{self.host} \" {cmd} \"'
            #print("findNumberOfTotalJobs: %s"%(cmd))

        nMyJobs = 1000000
        if DEBUG > 0:
            print(" CMD " + cmd)
        for line in os.popen(cmd).readlines():  # run command
            nMyJobs = int(line[:-1])

        if DEBUG > 0:
            print(" Jobs Counts - My: %d - Total: %d"%(nMyJobs,nJobs))

        return (nJobs,nMyJobs)

    #-----------------------------------------------------------------------------------------------
    # find the home directory where we submit
    #-----------------------------------------------------------------------------------------------
    def findHome(self,host,user):

        cmd = f'ssh -x {user}@{host} pwd'
        #print("findHome: %s"%(cmd))
        home = ''
        for line in os.popen(cmd).readlines():  # run command
            line = line[:-1]
            home = line
        #print("HOME: %s"%home)
        return home

    #-----------------------------------------------------------------------------------------------
    # find the user id where we submit
    #-----------------------------------------------------------------------------------------------
    def findRemoteUid(self,host,user):

        cmd = f'ssh -x {user}@{host} id -u'
        #print("findRemoteUid: %s"%(cmd))
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
            cmd = f"scp -q {localProxy} {self.user}@{self.host}:{remoteProxy}"
            print(cmd)
            os.system(cmd)

        return

    #-----------------------------------------------------------------------------------------------
    # show the scheduler parameters
    #-----------------------------------------------------------------------------------------------
    def show(self):

        print(' ====  S c h e d u l e r  ====')
        print(f' Here: {self.here}')
        print(f' Host: {self.host}')
        print(f' User: {self.user}')
        print(f' Base: {self.base}')
        print(f' HTCo: {str(self.condorVersion)}')
        print(' ===== ')
        print(' My  : %6d  (MMax: %d)'%(self.nMyTotal,self.nMyTotalMax))
        print(' Tot : %6d  (TMax: %d)'%(self.nTotal,self.nTotalMax))

    #-----------------------------------------------------------------------------------------------
    # update on the fly
    #-----------------------------------------------------------------------------------------------
    def update(self,host='submit05.mit.edu',user='paus',base='',nMyTotalMax=20000,nTotalMax=100000):

        self.host = host
        self.user = user
        self.nMyTotalMax = nMyTotalMax
        self.nTotalMax = nTotalMax
        if base == '':
            self.base = self.findHome(host,user)
        else:
            self.base = base
        self.ruid = self.findRemoteUid(host,user)

        self.updateNJobs()
        self.pushProxyToScheduler()

        return

    #-----------------------------------------------------------------------------------------------
    # update number of running jobs only
    #-----------------------------------------------------------------------------------------------
    def updateNJobs(self):
        (self.nTotal,self.nMyTotal) = self.findNumberOfTotalJobs()
        return

    #-----------------------------------------------------------------------------------------------
    # determine whether there is free capacity
    #-----------------------------------------------------------------------------------------------
    def hasFreeCapacity(self):
        # get most up-to-date numbers
        self.updateNJobs()
        # check whether my or total jobs are within limits
        if self.nMyTotal > self.nMyTotalMax or self.nTotal > self.nTotalMax:
            print(' NO CAPACITY: %d (nMyTotal)  %d (nTotal)\n'%(self.nMyTotal,self.nTotal))
            return False
        
        return True
