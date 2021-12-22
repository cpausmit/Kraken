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
Class:  Task(tag,config,version,sw,dataset,dbs,jobFile,siteFile)
Each task in condor is described in this class
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

        # create some useful shortcuts
        self.scheduler = self.request.scheduler
        self.sample = self.request.sample

        # derived
        self.activity = os.getenv('KRAKEN_ACTIVITY')
        self.swVersion = self.findSwVersion()
        self.osVersion = self.findOsVersion()
        self.nJobs = 0
        self.submitCmd = 'submit_' +  self.tag + '.cmd'
        self.logs = "%s/cms/logs/%s/%s/%s"%(self.scheduler.base, \
                                            self.request.config,self.request.version, \
                                            self.sample.dataset)
        self.outputData = "%s/cms/data/%s/%s/%s"%(self.scheduler.base, \
                                            self.request.config,self.request.version, \
                                            self.sample.dataset)
        self.tarBall = self.logs + '/kraken_' + self.swVersion + '.tgz'
        #self.tarBall = "http://t3serv001.mit.edu/~cmsprod/Kraken/agents/reviewd/%s/%s/kraken_%s.tgz"\
        #               %(self.request.config,self.request.version,self.swVersion)
        self.executable = self.logs + '/' + os.getenv('KRAKEN_SCRIPT')
        self.lfnFile = self.logs + '/' + self.sample.dataset + '.lfns'
        self.x509Proxy = self.findX509Proxy()

        # show what we got
        print('')
        self.show()
        print('')

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
        print(" INFO - removing submit script ")
        os.system("rm -rf " + self.submitCmd)

    #-----------------------------------------------------------------------------------------------
    # submit condor job
    #-----------------------------------------------------------------------------------------------
    def condorSubmit(self):

        # make sure this condorTask has jobs to be submitted
        if self.nJobs<1:
            print(' NO SUBMISSION: %d (nJobs)\n'%(self.nJobs))
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
        print(" INFO - update number of jobs on scheduler")
        if not self.scheduler.hasFreeCapacity():
            return False

        # we have free capacity log and output data dirs
        print(" INFO - make local directories ")
        cmd = "mkdir -p " + self.logs + " " + self.outputData
        if not self.scheduler.isLocal():
            cmd = 'ssh -x ' + self.scheduler.user + '@' + self.scheduler.host + ' ' + cmd
        os.system(cmd)

        # remember the remote data directories are created when copying started

        return True

    #-----------------------------------------------------------------------------------------------
    # find the present SW version
    #-----------------------------------------------------------------------------------------------
    def findSwVersion(self):
        cmd = "ls -1rt %s/%s/ |grep ^.*SW_"%(os.getenv('KRAKEN_SW'),self.request.version)
        print(" CMD: " + cmd)
        myRex = rex.Rex()
        (rc,out,err) = myRex.executeLocalAction(cmd)
        swVersion = ""
        for line in out.decode().split("\n"):
            if 'SW_' in line:
                swVersion = line
                swVersion = re.sub(r'^.*SW_', '', swVersion)

        print(" SW: " + swVersion)
        
        return swVersion

    #-----------------------------------------------------------------------------------------------
    # find the OS version of given SW release
    #-----------------------------------------------------------------------------------------------
    def findOsVersion(self):
        cmd = "ls -1 %s/%s/SW_%s/lib|cut -d_ -f1|tail -1"%\
            (os.getenv('KRAKEN_SW'),self.request.version,self.swVersion)
        #print(" CMD: " + cmd)
        myRex = rex.Rex()
        (rc,out,err) = myRex.executeLocalAction(cmd)
        osVersion = ""
        osVersion = out.decode()[:-1]
        if osVersion == "":
            osVersion = 'slc7'
        print(" OS: " + osVersion)

    
        return osVersion

    #-----------------------------------------------------------------------------------------------
    # find the present x509 proxy
    #-----------------------------------------------------------------------------------------------
    def findX509Proxy(self):
        cmd = "voms-proxy-info -path"
        #print " CMD: " + cmd
        myRex = rex.Rex()
        (rc,out,err) = myRex.executeLocalAction(cmd)
        x509Proxy = out[:-1]
        print " X509Proxy: " + x509Proxy
    
        return x509Proxy.split("/")[-1]

    #-----------------------------------------------------------------------------------------------
    # generate actual tarball, or leave as is if already up to date
    #-----------------------------------------------------------------------------------------------
    def makeTarBall(self):

        swBase = "%s/%s/%sSW_%s"%\
            (os.getenv('KRAKEN_SW'),self.request.version,os.getenv('KRAKEN_ACTIVITY').upper(),self.swVersion)

        # check if the tar ball exists locally
        if os.path.exists(swBase + "/kraken_" + self.swVersion + ".tgz"):
            print(" INFO - tar ball exists: " \
                + swBase + "/kraken_" + self.swVersion + ".tgz")
        else:
            print(' Make kraken tar ball: ' \
                + swBase + "/kraken_" + self.swVersion + ".tgz")

            cmd = "cd " + swBase \
                + "; tar fch kraken_" + self.swVersion + ".tar "
            if os.path.exists("%s/src/.git"%(swBase)):
                cmd += " --exclude=src/.git bin/ cfipython/ lib/ src/"
            else:
                cmd += ' --exclude=macros/.git *'
            #print(' CMD: ' + cmd)
            os.system(cmd)

            if os.path.exists("%s/python"%(swBase)):
                cmd = "cd " + swBase \
                      + "; tar fr kraken_" + self.swVersion + ".tar  python/"
                #print(' CMD: ' + cmd)
                os.system(cmd)

            if os.path.exists("%s/%s/%s"%(os.getenv('KRAKEN_BASE'),self.request.config,self.request.version)):
                cmd = "cd " + os.getenv('KRAKEN_BASE') \
                      + "; tar fr " + swBase + "/kraken_" + self.swVersion + ".tar tgz/ " \
                      + self.request.config + "/" + self.request.version
                #print(' CMD: ' + cmd)
                os.system(cmd)

            cmd = "cd " + swBase \
                + "; gzip kraken_" + self.swVersion + ".tar; mv  kraken_" \
                + self.swVersion + ".tar.gz  kraken_"  + self.swVersion + ".tgz"
            #print(' CMD: ' + cmd)
            os.system(cmd)

        # see whether the tar ball needs to be copied locally or to remote scheduler
        if self.scheduler.isLocal():
            cmd = "cp " + swBase+ "/kraken_" + self.swVersion + ".tgz " \
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
            ## also copy the proxy file
            #cmd = "cp -q /tmp/%s %s/"%(self.x509Proxy,self.logs)
            #os.system(cmd)
        else:
            cmd = "scp -q " + swBase + "/kraken_" + self.swVersion + ".tgz " \
                + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)
            cmd = "scp -q " + os.getenv('KRAKEN_BASE') + "/bin/" + os.getenv('KRAKEN_SCRIPT') \
                + " " + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)
            cmd = "scp -q " + os.getenv('KRAKEN_WORK') + '/lfns/' + self.sample.dataset + '.lfns' \
                + " " + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)
            #cmd = "scp -q /tmp/%s %s@%s:%s/"\
            #      %(self.x509Proxy,self.scheduler.user,self.scheduler.host,self.logs)
            #os.system(cmd)

        return

    #-----------------------------------------------------------------------------------------------
    # present the current condor task
    #-----------------------------------------------------------------------------------------------
    def show(self):

        print(' ==== C o n d o r  T a s k  I n f o r m a t i o n  ====')
        print(' ')
        print(' Tag          : ' + self.tag)
        print(' Base         : ' + self.request.base)
        print(' Config       : ' + self.request.config)
        print(' Version      : ' + self.request.version)
        print(' OS Version   : ' + self.osVersion)
        print(' SW Version   : ' + self.swVersion)
        print(' SW py        : ' + self.request.py)
        print(' ')
        self.sample.show()
        print(' ')
        self.scheduler.show()

    #-----------------------------------------------------------------------------------------------
    # write condor submission configuration
    #-----------------------------------------------------------------------------------------------
    def writeCondorSubmit(self):

        # make sure to keep track of the number of jobs created
        self.nJobs = 0

        # select requirement
        reqFile = os.getenv('KRAKEN_BASE') + '/condor/req-%s.sub '%(self.osVersion)
        if (os.getenv('KRAKEN_CONDOR_REQ') != ""):
            reqFile = '%s/condor/%s'%(os.getenv('KRAKEN_BASE'),os.getenv('KRAKEN_CONDOR_REQ'))
            print(" Hardwired condor requirements: %s"%(reqFile))

        # start with the base submit script
        cmd = 'cat %s %s/condor/base.sub > %s'%(reqFile,os.getenv('KRAKEN_BASE'),self.submitCmd)
        os.system(cmd)

        # attach the additional processing lines defining the specifc JOB productions
        with open(self.submitCmd,'a') as fileH:
            #fileH.write("Environment = \"HOSTNAME=" + os.getenv('HOSTNAME') + \
            #                "; KRAKEN_EXE=" + os.getenv('KRAKEN_EXE') + "\"" + '\n')
            # hardwired the hostname NOT GOOD NEEDS FIX
            fileH.write("Environment = \"SUBMIT_HOSTNAME=t3serv019.mit.edu; KRAKEN_EXE=%s\"\n"%os.getenv('KRAKEN_EXE'))
            fileH.write("Initialdir = " + self.outputData + '\n')
            fileH.write("Executable = " + self.executable + '\n')
            fileH.write("Log = %s/%s.log\n"%(self.logs,self.sample.dataset))
            fileH.write("transfer_input_files = %s,%s\n"%(self.tarBall,self.lfnFile))
            #fileH.write("transfer_input_files = %s,%s,%s/%s\n"%(self.tarBall,self.lfnFile,self.logs,self.x509Proxy))

            for (file,job) in self.sample.missingJobs.items():
                n = 0
                if file in self.sample.nFailedJobs:
                    n = self.sample.nFailedJobs[file]
                    if n > 2:
                        print(' %s --> n_failed: %d  skip processing'%(file,n))
                        continue
                print(' Adding(nF:%d): %s %s'%(n,file,job))
                self.nJobs += 1
                self.addJob(fileH,file,job)

        # make sure submit script is in the right place
        if not self.scheduler.isLocal() and self.nJobs>0:
            cmd = "scp -q " + self.submitCmd + " " \
                + self.scheduler.user + '@' +  self.scheduler.host + ':' + self.logs
            os.system(cmd)
