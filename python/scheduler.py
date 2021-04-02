#---------------------------------------------------------------------------------------------------
# Python Module File to describe the scheduler
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import os,socket
import rex

DEBUG = 0

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
    def __init__(self,
                 host='submit.mit.edu',user='paus',base='',
                 nMyTotalMax=20000,nTotalMax=100000):

        self.here = socket.gethostname()
        self.update(host,user,base,nMyTotalMax,nTotalMax)


    #-----------------------------------------------------------------------------------------------
    # execute a condor command on the given scheduler
    #-----------------------------------------------------------------------------------------------
    def executeCondorCmd(self,cmd='condor_q',output=False):

        if output:
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

        return (rc,out,err)

    #-----------------------------------------------------------------------------------------------
    # find number of all jobs on this scheduler
    #-----------------------------------------------------------------------------------------------
    def findNumberOfTotalJobs(self):

        cmd = 'condor_q -all|grep running|cut -d\' \' -f13|tail -1  2> /dev/null'
        if not self.isLocal():
            cmd = 'ssh -x ' + self.user + '@' + self.host + ' \"' + cmd + '\"'
            #print "findNumberOfTotalJobs: %s"%(cmd)

        nJobs = 1000000
        if DEBUG > 0:
            print " CMD " + cmd
        for line in os.popen(cmd).readlines():  # run command
            nJobs = int(line[:-1])

        cmd = 'condor_q ' + self.user + '|grep running|grep query|cut -d\' \' -f12 2> /dev/null'
        if not self.isLocal():
            cmd = 'ssh -x ' + self.user + '@' + self.host + ' \"' + cmd + '\"'
            #print "findNumberOfTotalJobs: %s"%(cmd)

        nMyJobs = 1000000
        if DEBUG > 0:
            print " CMD " + cmd
        for line in os.popen(cmd).readlines():  # run command
            nMyJobs = int(line[:-1])

        return (nJobs,nMyJobs)

    #-----------------------------------------------------------------------------------------------
    # find the home directory where we submit
    #-----------------------------------------------------------------------------------------------
    def findHome(self,host,user):

        cmd = 'ssh -x ' + user + '@' + host + ' pwd'
        #print "findHome: %s"%(cmd)
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

        cmd = 'ssh -x ' + user + '@' + host + ' id -u'
        #print "findRemoteUid: %s"%(cmd)
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
        print ' ===== '
        print ' My  : %6d  (MMax: %d)'%(self.nMyTotal,self.nMyTotalMax)
        print ' Tot : %6d  (TMax: %d)'%(self.nTotal,self.nTotalMax)

    #-----------------------------------------------------------------------------------------------
    # update on the fly
    #-----------------------------------------------------------------------------------------------
    def update(self,host='submit.mit.edu',user='paus',base='',nMyTotalMax=20000,nTotalMax=100000):

        self.host = host
        self.user = user
        self.nMyTotalMax = nMyTotalMax
        self.nTotalMax = nTotalMax


        #print(" BASE: <%s>"%base)
        if base == '':
            self.base = self.findHome(host,user)
        else:
            self.base = base
        self.ruid = self.findRemoteUid(host,user)
        (self.nTotal,self.nMyTotal) = self.findNumberOfTotalJobs()
        

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
            print ' NO CAPACITY: %d (nMyTotal)  %d (nTotal)\n'%(self.nMyTotal,self.nTotal)
            return False
        
        return True
