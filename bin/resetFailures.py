#!/usr/bin/env python
import os,sys
from optparse import OptionParser

if os.getenv('KRAKEN_AGENTS_LOG'):
    agent_log = os.getenv('KRAKEN_AGENTS_LOG')
    agent_www = os.getenv('KRAKEN_AGENTS_WWW')
else:
    print(" ERROR - agents are not setup.")
    sys.exit(1)

# define and get all command line arguments
parser = OptionParser()
parser.add_option("-c", "--config", dest="config", default='*',  help="MIT internal config")
parser.add_option("-v", "--version",dest="version",default='*',  help="MIT Internal version")
parser.add_option("-p", "--pattern",dest="pattern",default='*',  help="MIT Internal dataset pattern")
parser.add_option("-a", "--all",    dest="all",    default=False,help="all productions", action="store_true")
parser.add_option("-e", "--exec",   dest="exec",   default=False,help="execute", action="store_true")
(options, args) = parser.parse_args()

if options.all:
    cmd_local = "%s/reviewd/??????/???/*%s*/ncounts.err"%(agent_log,options.pattern)
    cmd_html = "%s/reviewd/??????/???/*%s*/ncounts.err"%(agent_www,options.pattern)
else:
    cmd_local = "%s/reviewd/%s/%s/*%s*/ncounts.err"%(agent_log,options.config,options.version,options.pattern)
    cmd_html = "%s/reviewd/%s/%s/*%s*/ncounts.err"%(agent_www,options.config,options.version,options.pattern)

print("\n Pattern - LOCAL: %s\n"%cmd_local)
os.system("ls %s"%cmd_local)
if options.exec:
    os.system("rm %s"%cmd_local)
print("\n Pattern - HTML: %s\n"%cmd_html)
os.system("ls %s"%cmd_html)
if options.exec:
    os.system("rm %s"%cmd_html)
