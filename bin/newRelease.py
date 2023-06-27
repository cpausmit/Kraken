#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
# Make a new release directory
#
# v1.0                                                                                  Mar 27, 2023
#---------------------------------------------------------------------------------------------------
import sys,os,getopt,time
from optparse import OptionParser

#===================================================================================================
#                                         M A I N
#===================================================================================================

# --------------------------------------------------------------------------------------------------
# Get all parameters for the production
# --------------------------------------------------------------------------------------------------
# define and get all command line arguments
parser = OptionParser()
parser.add_option("-c","--config",dest="config",default='',help="configuration")
parser.add_option("-v","--version",dest="version",default='',help="version")
parser.add_option("-p","--previous",dest="previous",default='',help="previous version")
(options, args) = parser.parse_args()

if options.config == '' or options.version == '':
    print(' ERROR - specify config (-c) and version (-v).')
    sys.exit()

# say what we are looking at
print('')
print(' Config:  %s'%(options.config))
print(' Version: %s'%(options.version))
print('')

WORK = os.environ.get('KRAKEN_WORK')
BASE = os.environ.get('KRAKEN_BASE')

cmd = 'mkdir %s/%s/%s'%(WORK,options.config,options.version)
print(' CMD: ' + cmd)
os.system(cmd)

if options.previous != '':
    cmd = 'cp -r %s/%s/%s %s/%s/%s'\
          %(BASE,options.config,options.previous,
            BASE,options.config,options.version)
else:
    cmd = 'mkdir %s/%s/%s'%(BASE,options.config,options.version)

print(' CMD: ' + cmd)
os.system(cmd)
