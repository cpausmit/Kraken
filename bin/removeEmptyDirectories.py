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

#---------------------------------------------------------------------------------------------------
#  M A I N
#---------------------------------------------------------------------------------------------------
book = sys.argv[1]

# hi, here we are!
os.system("date")

# make a list of all tmp directories
allDirs = []
print ' Find all sample directories.'

# - get all directories
cmd = 'list ' + DIR + "/" + book + "| cut -d' ' -f2"
if DEBUG>0:
    print ' CMD: ' + cmd
emptyDirs = {}
for line in os.popen(cmd).readlines():
    #print "%s"%line[:-1]
    emptyDirs[line[:-1]] = True

cmd = 'list ' + DIR + "/" + book + "/*/ | grep .root | cut -d' ' -f2"
print ' CMD: ' + cmd
for line in os.popen(cmd).readlines():
    line = line[:-1]
    f = line.split("/")
    sample = "/".join(f[:-1])
    filename = f[-1]
    if sample in emptyDirs:
        emptyDirs[sample] = False
    else:
        print " ERROR -- sample was not found to begin with?!"

for key in emptyDirs:
    cmd = 'removedir ' + key
    if emptyDirs[key]:
        print " Removing - %s"%(key)
        os.system(cmd)
    else:
        print " Not empty - %s"%(key)
