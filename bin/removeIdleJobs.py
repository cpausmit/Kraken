#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------------
# Script to remove all idle jobs in our scheduler to let all newly submitted jobs use new
# parameters.
#
# Author: C.Paus                                                                     (June 16, 2016)
#---------------------------------------------------------------------------------------------------
import os,sys,getopt,re,string
from scheduler import Scheduler
 
#===================================================================================================
# M A I N
#===================================================================================================
# Define string to explain usage of the script
usage =  "Usage: removeIdleJobs.py --local  # submitting to the local scheduler (ex. t3serv015)\n"
usage += "                         --help\n"

# Define the valid options which can be specified and check out the command line
valid = ['local','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# Set defaults for each command line parameter/option
local = False

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--local":
        local = True

# Setup the scheduler we are going to use
scheduler = None
user = 'cmsprod'
if local:
    scheduler = Scheduler('t3serv015.mit.edu',user)
else:
    scheduler = Scheduler(os.getenv('KRAKEN_CONDOR_SCHEDD'),os.getenv('KRAKEN_REMOTE_USER'),'/work/submit/paus')

# Issue the condor command
cmd = 'condor_rm -constraint "JobStatus==1&&Owner==\\"'+user+'\\""'
scheduler.executeCondorCmd(cmd,True)

sys.exit(0)
