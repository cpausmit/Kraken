#!/usr/bin/env python
#==================================================================================================
#
# Script to remove all log files of successfully completed jobs and analysis of all failed jobs and
# remove the remaining condor queue entires of the held jobs.
#
# We are assuming that any failed job is converted into a held job. We collect all held jobs from
# the condor queue and safe those log files into our web repository for browsing. Only the last
# copy of the failed job is kept as repeated failure overwrites the old failed job's log files. The
# held job entries in the condor queue are removed on the failed job is resubmitted.
#
# It should be noted that if a job succeeds all log files including the ones from earlier failures
# will be removed.
#
#==================================================================================================
import os,sys,subprocess,getopt

def getValue(line):
    value = line.replace('\n','')
    value = (value.split("="))[1]
    value = value.replace('"','')
    value = value.strip()
    return value

def findAllJobStubs(dir,debug=0):
    # find all job file stubs (without .err/.out extensions) to analyze
    
    cmd = "ls %s/*.err"%(dir)
    if debug > 0:
        print(" CMD: " + cmd)
    
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode
    
    if debug > 0:
        print("\n\n RC : " + str(rc))
        print("\n\n OUT:\n" + out)
        print("\n\n ERR:\n" + err)
    
    out = out.decode().replace('.err','')
    stubs = (out[:-1]).split("\n")                 # make sure to ignore the last '\n'
    print(' Number of all jobs found: %d'%(len(stubs)))

    return stubs

def readPatterns(debug=0):
    # read the patterns to search for in error and output files

    with open(os.getenv('KRAKEN_ERROR_DB'),"r") as f:
        input = f.read()
        data = eval(input)
    
    if debug > 0:
        print(" PATTERNS: ")
        print(data)

    oPs = data['outPatterns']
    ePs = data['errPatterns']

    return (oPs, ePs)

def isValidStub(stub):

    if stub == '':
        return False
    if stub[-7:] == 'ncounts':
        return False

    if not os.path.exists(stub+'.out') or not os.path.exists(stub+'.err'):
        print(' Output/Error file not available: ' + stub + ' ' + stub[-7:])
        return False

    return True


#---------------------------------------------------------------------------------------------------
#                                         M A I N
#---------------------------------------------------------------------------------------------------
# Define the valid options which can be specified and check out the command line
usage = "\n analyzeLogs.py --dir=<directory>  [ --debug=<int> ]\n"
valid = ['dir=','debug=','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# Set defaults for each command line parameter/option
    
# general parameters
debug = 0
dir = './'

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)
    if opt == "--dir":
        dir = arg
    if opt == "--debug":
        debug = arg

# get the patterns to look for
(outPatterns, errPatterns) = readPatterns(debug)

# get the job file stubs to analyze
stubs = findAllJobStubs(dir,debug)

# # loop through the job stubs
for stub in stubs:
 
    if not isValidStub(stub):
        continue

    if debug > -1:
        print(" Open: %s"%(stub+'.out'))

    # first analyze the output
    with open(stub+'.out',"r") as f:
        for line in f:
            for tag,value in iter(outPatterns.items()):
                if value in line:
                    outCounts[tag] += 1
                    if tag == 'node':
                        if line.startswith(value):
                            hostName = getValue(line)
                    if tag == 'glideinSe':
                        se = getValue(line)
                    if tag == 'glidein':
                        siteName = getValue(line)
