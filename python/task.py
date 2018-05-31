#---------------------------------------------------------------------------------------------------
# Python Module File to describe task
#
# Author: C.Paus                                                                      (Jun 16, 2016)
#---------------------------------------------------------------------------------------------------
import os,sys,re,string,socket
import rex
from request import Request
from sample import Sample

DEBUG = 0

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
        if self.nJobs<1:
            print ' NO SUBMISSION: %d (nJobs)\n'%(self.nJobs)
            return

        # start with the base submit script
        cmd = 'condor_submit ' +  self.submitCmd
        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host \
                + ' \"cd ' + self.logs + '; ' + cmd + '\"'
        os.system(cmd)

        # make sure to keep track of the updated number of jobs in the system
        self.scheduler.updateNJobs()

    #-----------------------------------------------------------------------------------------------
    # create the required local and remote directories
    #-----------------------------------------------------------------------------------------------
    def createDirectories(self):

        # make sure to keep track of the updated number of jobs in the system
        print " INFO - update number of jobs on scheduler"
        if not self.scheduler.hasFreeCapacity():
            return False

        # we have free capacity log and output data dirs
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

        return True

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
                + "; tar fch kraken_" + self.cmsswVersion + ".tar bin/ cfipython/ lib/ src/"
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
        cmd = 'cat ' + os.getenv('KRAKEN_BASE') + '/condor/req-allNoEaps.sub ' \
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
