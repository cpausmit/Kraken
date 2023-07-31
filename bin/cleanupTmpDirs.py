#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
#
# Find all left over temporary directories on Tier-2 and remove them.
#
#---------------------------------------------------------------------------------------------------
import os,sys
from rex import Rex

PREFIX = os.getenv('KRAKEN_TMP_PREFIX')
DEBUG = int(os.environ.get('T2TOOLS_DEBUG',0))
DIR = "/cms/store/user/paus"

def findActiveStubs():

    cmd = 'condor_q -constraint "JobStatus!=5" -format "%s\\n" Args|cut -d\' \' -f8'
    myRx = rex.Rex(os.getenv('KRAKEN_CONDOR_SCHEDD'),os.getenv('KRAKEN_REMOTE_USER'))
    irc = 0

    #print " CMD : " + cmd
    (irc,rc,out,err) = myRx.executeAction(cmd)
    if (irc != 0 or rc != 0):
        print ' ERROR -- IRC: %d'%(irc) 
        print ' ERROR -- RC:  %d'%(rc) 
        print ' ERROR -- ERR:\n%s'%(err) 

    #print ' OUT:\n%s'%(out) 
    #if err!='':
    #    print '\n ERR:\n%s'%(err) 

    stubs = []
    stubs = out.split("\n")
    
    return stubs

def cleanupBook(book,activeStubs):

    # make a list of all tmp directories
    allTmpDirs = []
    print ' Find all tmp directories in book: %s.'%(book)
    
    cmd = 'list ' + DIR + "/" + book + "/*/ | grep %s"%(PREFIX)
    if DEBUG>0:
        print ' CMD: ' + cmd
    
    for line in os.popen(cmd).readlines():
        f = (line[:-1].split("/"))[-2:]
        stub = f[-1]
        sample = "/".join(f)
        if stub in activeStubs:
            print ' Active stub will not be touched: ' + stub
        else:
            allTmpDirs.append(sample)
            print ' Found directory: ' + sample
    
    # say what we found
    print ' --> number of stubs to delete: %d'%(len(allTmpDirs))
    
    for sample in allTmpDirs:
        cmd = 'removedir ' + DIR + "/" + book + "/" + sample
        if DEBUG>0:
            print ' CMD: ' + cmd
        # make sure it really is just the tmp directory
        if cmd.find(PREFIX) != -1:
            os.system(cmd)
        else:
            print ' ERROR -- it looks like a wrong directory was up for deletion.'
            print '       -- directory:  %s  is not deleting a tmp directory.'%(cmd)
            sys.exit(1)
    

#---------------------------------------------------------------------------------------------------
#  M A I N
#---------------------------------------------------------------------------------------------------
books = sys.argv[1:]
activeStubs = findActiveStubs()

# hi, here we are!
os.system("date")

for book in books:
    cleanupBook(book,activeStubs)
