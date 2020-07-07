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

def addSite(siteTag,nErrsSites):
    # add a new site to the mix

    if siteTag in nErrsSites:
        nErrsSites[siteTag] += 1
    else:
        nErrsSites[siteTag] = 1
    return nErrsSites

def addErrorAtSite(errorTag,siteTag,nErrsSitesTypes):
    # add one error count for a given error type at a given site

    if errorTag in nErrsSitesTypes:
        nErrsSitesTypes[errorTag] = addSite(siteTag,nErrsSitesTypes[errorTag])
    else:
        # first appearence of error tag
        nErrsSites = {}
        nErrsSites[siteTag] = 1
        nErrsSitesTypes[errorTag] = nErrsSites
 
    return nErrsSitesTypes

def printErrorAtSite(nErrsSitesTypes):

    # find all site tags
    siteTags = []
    for errTag,nErrsSite in nErrsSitesTypes.iteritems():
        for siteTag in nErrsSite:
            if siteTag not in siteTags:
                siteTags.append(siteTag)

    sys.stdout.write(" %-10s "%('=========='))
    for siteTag in siteTags:
        sys.stdout.write("%10s "%siteTag[:10])        


    for errTag,nErrsSite in nErrsSitesTypes.iteritems():
        sys.stdout.write("\n %-10s "%errTag)
        for siteTag in siteTags:
            if siteTag in nErrsSite:
                sys.stdout.write("%10d "%(nErrsSite[siteTag]))
            else:
                sys.stdout.write("%10d "%(0))
    print ''

    return

def findHeldJobStubs(config,version,dataset,debug=0):
    # find all job file stubs (without .err/.out extensions) to analyze

    
    cmd = "ls " + os.getenv('KRAKEN_AGENTS_WWW') + "/reviewd/%s/%s/%s/*.err" \
        %(config,version,dataset)
    if debug > 0:
        print " CMD: " + cmd
    
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    rc = p.returncode
    
    if debug > 0:
        print "\n\n RC : " + str(rc)
        print "\n\n OUT:\n" + out
        print "\n\n ERR:\n" + err
    
    out = out.replace('.err','')
    stubs = (out[:-1]).split("\n")                 # make sure to ignore the last '\n'
    print ' Number of failed jobs found: %d'%(len(stubs))

    return stubs

def readPatterns(debug=0):
    # read the patterns to search for in error and output files

    with open(os.getenv('KRAKEN_ERROR_DB'),"r") as f:
        input = f.read()
        data = eval(input)
    
    if debug > 0:
        print " PATTERNS: "
        print data

    oPs = data['outPatterns']
    ePs = data['errPatterns']

    return (oPs, ePs)

def isValidStub(stub):

    if stub == '':
        return False

    if not os.path.exists(stub+'.out') or  not os.path.exists(stub+'.err'):
        print ' Output/Error file not available: ' + stub
        return False

    return True


#---------------------------------------------------------------------------------------------------
#                                         M A I N
#---------------------------------------------------------------------------------------------------
if not os.getenv('KRAKEN_AGENTS_WWW'):
    print "\n Kraken agent environment is not initialized (KRAKEN_AGENTS_WWW).\n"
    sys.exit(1)

# Define the valid options which can be specified and check out the command line
usage = "\n analyzeErrors.py --config=<cfg>  --version=<vrs>  --dataset=<dset>"\
    + "  [ --debug=<int> [ --interactive ] ]\n"
valid = ['config=','version=','dataset=','debug=','interactive','help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError, ex:
    print usage
    print str(ex)
    sys.exit(1)

# Set defaults for each command line parameter/option
    
# general parameters
debug = 0
interactive = False
config = 'pandaf'
version = '001'
dataset = ''

# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print usage
        sys.exit(0)
    if opt == "--config":
        config = arg
    if opt == "--version":
        version = arg
    if opt == "--dataset":
        dataset = arg
    if opt == "--debug":
        debug = int(arg)
    if opt == "--interactive":
        interactive = True

# get the patterns to look for
(outPatterns, errPatterns) = readPatterns(debug)

# keep track of sites showing errors
nErrsSites = {}

# keep track of output file patterns
outCounts = {}
outValues = {}
for tag,value in outPatterns.iteritems():
    outCounts[tag] = 0
    outValues[tag] = ''

# keep track of error file patterns
errCounts = {}
errValues = {}
for tag,value in errPatterns.iteritems():
    errCounts[tag] = 0
    errValues[tag] = ''

nErrsSitesTypes = {}

# get the job file stubs to analyze
stubs = findHeldJobStubs(config,version,dataset,debug)

# loop through the job stubs
for stub in stubs:

    if not isValidStub(stub):
        continue

    se  = 'undefined'
    siteName = 'undefined'
    hostName = 'undefined'

    if debug > 1:
        print " Open: %s"%(stub+'.out')

    # first analyze the output
    with open(stub+'.out',"r") as f:
        for line in f:
            for tag,value in outPatterns.iteritems():
                if value in line:
                    outCounts[tag] += 1
                    if tag == 'node':
                        if line.startswith(value):
                            hostName = line[:-1].split("=")[1]
                    if tag == 'glideinSe':
                        se = line.replace('\n','')                       
                    if tag == 'glidein':
                        siteName = line.replace('\n','')
                        siteName = (siteName.split("="))[1]
 
    errTag = 'ud'
    lError = False
    if debug > 1:
        print " Open: %s"%(stub+'.err')
    with open(stub+'.err',"r") as f:
        for line in f:
            for tag,value in errPatterns.iteritems():
                if value in line:
                    lError = True
                    errTag = tag
                    errCounts[tag] += 1
                    #errValues[tag] += line
                    if debug>0:
                        print " ERR(%s) on %s in stub %s"%(errTag,hostName,stub)
                    if debug>1:
                        print " ERR %s"%(line[:-1])

    if siteName in nErrsSites:
        pass
    else:
        nErrsSites[siteName] = 0

    if lError:
        nErrsSites[siteName] += 1

    if errTag != 'ud':
        nErrSitesTypes = addErrorAtSite(errTag,siteName,nErrsSitesTypes)

print ''
print ' ---- ERROR SUMMARY ----'
print '  error tag       count '
print ' ======================='
nTotal = 0
for tag in sorted(errPatterns):
    print '  %-14s: %4d'%(tag,errCounts[tag])
    nTotal += errCounts[tag]
print ' ---------------------------------'
print '  %-14s: %4d'%('TOTAL',nTotal)
print ' ================================='
print ''
print ''
print ' ------ ERROR SUMMARY SITE -------'
print '  site tag                  count '
print ' ================================='
nTotal = 0
for tag in sorted(nErrsSites):
    print '  %-25s: %4d'%(tag,nErrsSites[tag])
    nTotal += nErrsSites[tag]
print ' ---------------------------------'
print '  %-25s: %4d'%('TOTAL',nTotal)
print ' ================================='
print ''

print ' Err Matrix'
printErrorAtSite(nErrsSitesTypes)
print ''

if sys.stdin.isatty() and interactive:
    # running interactively
    answer = raw_input('Wanna watch error files? [N/y] ')
else:
    sys.exit(0)

# go through the output and error files
for stub in stubs:

    if stub == '':
        continue

    if not os.path.exists(stub+'.out') or  not os.path.exists(stub+'.err'):
        print ' Output/Error file not available: ' + stub
        continue

    if debug > 1:
        print " Open: %s"%(stub+'.err')

    with open(stub+'.err',"r") as f:
        for line in f:
            print line[:-1]
        print ' File: %s.%s'%(stub,'err')
        answer = raw_input('Remove this held job? [N/y] ')

if len(sys.argv) < 2:
    print ' End (%d)'%(len(sys.argv))
    print ' A: ' + sys.argv[0]
    sys.exit(0)
elif sys.argv[1] == 'remove':
    pass
else:
    print ' Done (%d)'%(len(sys.argv))
    sys.exit(0)

cmd = "condor_q " + os.getenv('USER') \
    + " -constrain HoldReasonCode!=0 -format %s: ClusterId -format %s: ProcId -format %s\n Err"
list = cmd.split(" ")
p = subprocess.Popen(list,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(out, err) = p.communicate()
rc = p.returncode

out = out.replace('.err','')
lines = out.split("\n") 
for line in lines:
    f = line.split(":")
    print ' Line: ' + line

    if len(f) < 2:
        continue

    clusterId = f[0]
    procId = f[1]
    stub = f[2]

    cmd = ' rm ' + stub + ".*; condor_rm " + clusterId + "." + procId
    print cmd
    os.system(cmd)
