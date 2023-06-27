#!/usr/bin/env python
# ---------------------------------------------------------------------------------------------------
# Script to synchronize the agents work logs with the web page. Should be as light weight as
# possible because it needs to run frequently.
#
# Author: C.Paus                                                                      (Dec 21, 2016)
#---------------------------------------------------------------------------------------------------
import os,sys,re,getopt
import rex

#===================================================================================================
# Main starts here
#===================================================================================================
# Define string to explain usage of the script
usage = "\nUsage: sycnhronizeWeb.py [ --help ]\n"

# Define the valid options which can be specified and check out the command line
valid = ['help']
try:
    opts, args = getopt.getopt(sys.argv[1:], "", valid)
except getopt.GetoptError as ex:
    print(usage)
    print(str(ex))
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Get all parameters for this little task
# --------------------------------------------------------------------------------------------------
# Read new values from the command line
for opt, arg in opts:
    if opt == "--help":
        print(usage)
        sys.exit(0)

# Deal with obvious problems
if not os.getenv('KRAKEN_AGENTS_WWW'):
    print("\n Kraken agent environment is not initialized (KRAKEN_AGENTS_WWW).\n")
    sys.exit(1)

# --------------------------------------------------------------------------------------------------
# Here is where the real action starts -------------------------------------------------------------
# --------------------------------------------------------------------------------------------------
myRx = rex.Rex()

# make sure to touch the heartbeat file first
cmd = "date >& " + os.getenv('KRAKEN_AGENTS_LOG')  + '/heartbeat'
(rc,out,err) = myRx.executeLocalAction(cmd)

# update our cycle info (needed for the active productions)
cmd = "cp  " + os.getenv('KRAKEN_AGENTS_BASE') + "/cycle.cfg " + os.getenv('KRAKEN_AGENTS_LOG')
(rc,out,err) = myRx.executeLocalAction(cmd)

if rc != 0:
    print('\n ==== ERROR -- DATE (%s) ====\n\n%s'%(cmd,err))
    print('\n ==== OUTPUT -- DATE (%s) ====\n\n%s'%(cmd,out))
else:
    print(' ==== DATE (%s) ===='%(cmd))

# issue full rsync on the log directory
cmd = "rsync -Cavz --delete " + os.getenv('KRAKEN_AGENTS_LOG') + ' ' \
    +                           os.getenv('KRAKEN_AGENTS_WWW') + '/../'
print(' Synchronizing: %s'%(cmd))

rc = 0
out = ''
err = ''
(rc,out,err) = myRx.executeLocalAction(cmd)

if rc != 0:
    print('\n ==== ERROR -- RSYNC (%s) ====\n\n%s'%(cmd,err))
    print('\n ==== OUTPUT -- RSYNC (%s) ====\n\n%s'%(cmd,out))
else:
    print('\n ==== RSYNC (%s) ====\n\n%s'%(cmd,out))
