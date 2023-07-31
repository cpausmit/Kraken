#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Show a summary of what is cooking in the queues.
#
# v1.0                                                                                  Feb 22, 2023
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import rex
import jobsummary
from optparse import OptionParser

def findAllJobs(config,version):
    # find information about all jobs in the queue
    cmd  = "condor_q -nobatch -cputime | tr -s ' ' | grep paus | grep -v ^Total"
    if config != '' and version != '':
        cmd += " | grep ' %s %s '"%(config,version)
    #cmd = "condor_q -format \"\%d \" ClusterId -format \"\%d \" JobStatus -format \"\%s\n\" Args"
    print(" Output based on: %s\n"%(cmd))
    myRx = rex.Rex(os.getenv('KRAKEN_CONDOR_SCHEDD'),os.getenv('KRAKEN_REMOTE_USER'))
    (irc,rc,out,err) = myRx.executeLongAction(cmd)

    return out.split("\n")

def runningTime(string):
    # typical format 0+01:54:15
    days = int(string.split('+')[0])
    hours = int(string.split('+')[1].split(':')[0])
    minutes = int(string.split('+')[1].split(':')[1])
    seconds = int(string.split('+')[1].split(':')[2])
    return days*86400+hours*3600+minutes*60+seconds

def jobStatus(string):
    # convert job status string to the jobs status integer
    jobstatus = 0
    if   string == "I":
        jobstatus = 1
    elif string == "R":
        jobstatus = 2
    elif string == "E":
        jobstatus = 3
    elif string == "C":
        jobstatus = 4
    elif string == "H":
        jobstatus = 5
        
    return jobstatus
        

#===================================================================================================
# Main starts here
#===================================================================================================
# define and get all command line arguments
parser = OptionParser()
parser.add_option("-c", "--config",dest="config",default='',help="configuration")
parser.add_option("-v", "--version",dest="version",default='',help="version")
(options, args) = parser.parse_args()

# date it
os.system("date")
print("===============================")

# find files and cataloged entries
jobs = findAllJobs(options.config,options.version)

jobsummaries = {}
for job in jobs:
    f = job.split(" ")
    if len(f)<5 or 'Schedd' in job:
        continue

    if options.config != '' and options.version != '':
        key = "%s"%(f[13])
    else:
        key = "%s:%s:%s:%s"%(f[10],f[11],f[12],f[13])

    if key not in jobsummaries:
        jobsummaries[key] = jobsummary.Jobsummary(key)
    jobsummaries[key].add_job(jobStatus(f[5]),runningTime(f[4]))
    
first = True
for key, value in sorted(jobsummaries.items()):
    value.show(first)
    first = False
    
sys.exit(0)
