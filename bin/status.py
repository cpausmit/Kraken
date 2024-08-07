#!/usr/bin/python
#---------------------------------------------------------------------------------------------------
# Show a summary of what is gogin on in the cycle.
#
# v1.0                                                                                  Feb 22, 2023
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
import rex
import jsum
import timeseries
import kdb
from optparse import OptionParser

def storeStatus(epoch,key,jsum):
    # store the status of a given request into a file, append to the existing record
    f = key.split("-")
    config = f[0]
    version = f[1]
    dataset = "-".join(f[2:])
    cmd = "mkdir -p %s/moni/%s/%s/"%(os.getenv('KRAKEN_WORK'),config,version)
    os.system(cmd)
    output = "%s/moni/%s/%s/%s.moni"%(os.getenv('KRAKEN_WORK'),config,version,dataset)
    os.system("touch %s"%(output))
    with open(output,'a') as f:
        f.write("%d,%s\n"%(epoch,jsum.string()))
    return

def harvestAllCampaigns(cycle):
    # get all processing requests from the campaigns in the given cycle
    campaigns = []
    requests = []
    # find all relevant requests to review
    print(" Harvest all campaigns from Tier-2")
    cmd = "list /cms/store/user/paus/??????/"
    myRx = rex.Rex(None,None)
    (rc,out,err) = myRx.executeLocalAction(cmd)
    for campaign in out.split("\n"):
        f = campaign.split("/")
        if len(f) < 7:
            continue
        config = f[-2]
        version = f[-1]
        campaigns.append("%s-%s"%(config,version))
        db = kdb.Kdb()
        for row in db.find_requests(config,version):
            dataset = "%s+%s+%s"%(row[0],row[1],row[2])
            requests.append("%s:%s:%s"%(config,version,dataset))
    return campaigns,requests

def findNoCatalog(base):
    # list all files that are not in the catalog
    data = []
    print(" Find not cataloged files")
    input = "/tmp/nocatalog.list"
    cmd = "list %s/*/???/*/tmp_* > %s"%(base,input)
    os.system(cmd)
    with open(input,'r') as f:
        data = f.read()
    return data

def findAllJobs(config,version):
    # find information about all jobs in the queue
    cmd  = "condor_q -nobatch -cputime | tr -s ' ' | grep paus | grep -v ^Total"
    if config != '' and version != '':
        cmd += " | grep ' %s %s '"%(config,version)
    print(" Review condor queue")
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
parser.add_option("-d", "--debug",dest="debug",default=0,help="debugging level")
(options, args) = parser.parse_args()

BASE = os.getenv('KRAKEN_SE_BASE')
CATALOG = os.getenv('KRAKEN_CATALOG_OUTPUT')
JOBS = os.getenv('KRAKEN_WORK') + '/jobs'
MONI = os.getenv('KRAKEN_WORK') + '/moni'
EPOCH = int(time.time())

# date it
os.system("date")
print("===============================")

jobsummaries = {}

cycle = os.environ.get('KRAKEN_REVIEW_CYCLE','')
(campaigns,requests) = harvestAllCampaigns(cycle)

# the nocatalog file is done once
data = findNoCatalog(BASE)

for request in requests:
    config,version,dataset = request.split(":")
    
    # make sure to only consider the requested requests
    if config != options.config and options.config != '':
        continue
    if version != options.version and options.version != '':
        continue

    # form the unique key
    key = "%s-%s-%s"%(config,version,dataset)

    input = "%s/%s.jobs"%(JOBS,dataset)
    count = -1
    if os.path.exists(input):
        with open(input,'r') as f:
            for count, line in enumerate(f):
                pass
    n_total = count + 1

    db = kdb.Kdb()
    n_done = db.find_files_done(config,version,dataset).getSize()
    
    n_nocatalog = 0
    for line in data.split("\n"):
        if "%s/%s/%s"%(config,version,dataset) in line:
            n_nocatalog += 1
            
    # make a new entry in our job summaries
    jobsummaries[key] = jsum.Jsum()
    jobsummaries[key].set_totals(n_total,n_done,n_nocatalog)

# find files and cataloged entries
jobs = findAllJobs(options.config,options.version)

for job in jobs:
    f = job.split(" ")
    if len(f)<5 or 'Schedd' in job:
        continue

    key = "%s-%s-%s"%(f[10],f[11],f[13])
    if key not in jobsummaries:
        print(" WARNING - found a key (%s) not defined in any ongoing campaign!"%(key))
        print(" WARNING - jobsummary will not be stored and jobs in batch are not monitored!")
    else:
        jobsummaries[key].add_job(jobStatus(f[5]),runningTime(f[4]))
    
first = True
for key, value in sorted(jobsummaries.items()):
    value.show(key,first)
    first = False

    storeStatus(EPOCH,key,value)
    cmd = "progress.py -w -q -n %s -x 'epoch time [sec]' -y 'files processing'"%(key)
    if options.debug < 1:
        cmd += " >& /dev/null"
    os.system(cmd)

for campaign in campaigns:
    if (options.config in campaign or options.config == '') and (options.version in campaign or options.version == ''):
        print(" PROCESS - %s"%(campaign))
        cmd = "progress.py -w -q -n %s -x 'epoch time [sec]' -y 'files processing'"%(campaign)
        if options.debug < 1:
            cmd += " >& /dev/null"
        os.system(cmd)
    
sys.exit(0)
