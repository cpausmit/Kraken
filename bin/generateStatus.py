#!/usr/bin/env python
#---------------------------------------------------------------------------------------------------
# Generate status.json for the Kraken monitoring dashboard (agents/dashboard/). This is the
# read-only status generator that the dashboardd daemon loops on; it never touches condor, the
# DB, or the filesystem beyond reading them.
#
# Author: C.Paus                                                                      (Sep 01, 2026)
#---------------------------------------------------------------------------------------------------
import os, time
from optparse import OptionParser

import dashboard

#---------------------------------------------------------------------------------------------------
#                                         M A I N
#---------------------------------------------------------------------------------------------------
parser = OptionParser()
parser.add_option("--agents-log", dest="agentsLog",
                   default=os.getenv('KRAKEN_AGENTS_LOG'), help="Kraken agents log area")
parser.add_option("--agents-base", dest="agentsBase",
                   default=os.getenv('KRAKEN_AGENTS_BASE'), help="Kraken agents install area")
parser.add_option("--schedd", dest="schedds", action="append", default=None,
                   help="condor scheduler host (repeatable).  OFF by default: the batch "
                        "counts come from the queue files the Kraken services write.  Give "
                        "this only to query condor directly, which then overrides them.")
parser.add_option("--checkfile-db", dest="checkfileDb",
                   default='/home/tier3/cmsprod/cms/logs/fibs/checkFile/checkFileActivity.db',
                   help="checkFile activity flat-file DB")
parser.add_option("--out", dest="out", default='', help="output status.json path")
parser.add_option("--heartbeat-warn", dest="heartbeatWarn", default=900, type="int",
                   help="heartbeat age [s] before status turns 'stale'")
parser.add_option("--heartbeat-dead", dest="heartbeatDead", default=3600, type="int",
                   help="heartbeat age [s] before status turns 'dead'")
parser.add_option("-d", "--debug", dest="debug", default=0, type="int", help="debug level")
(options, args) = parser.parse_args()

if not options.agentsLog:
    raise SystemExit(" ERROR - KRAKEN_AGENTS_LOG is not set and --agents-log was not given.")
if not options.out:
    options.out = os.path.join(options.agentsLog, 'status.json')
# No condor query unless one is asked for explicitly.  Every number on the dashboard is
# meant to come from the monitoring files the Kraken services themselves write; going to a
# second source risks the page disagreeing with the files for reasons nobody can see.  The
# defaults here also did not work: socket.gethostname() is t3desk000, which is not a schedd
# ("Collector has no record of schedd/submitter"), and KRAKEN_CONDOR_SCHEDD=submit04.mit.edu
# reports 0 jobs, while the jobs actually sit on the default schedd.  That is what left
# BATCH/IDLE/RUN/HELD reading zero on every sample.
if not options.schedds:
    options.schedds = []

heartbeat_path = os.path.join(options.agentsLog, 'heartbeat')
cycle_cfg = os.path.join(options.agentsBase or '', 'cycle.cfg')

(hb_health, hb_age) = dashboard.heartbeat_health(heartbeat_path, options.heartbeatWarn, options.heartbeatDead)
active_pys = dashboard.parse_review_cycle(cycle_cfg)

campaigns = dashboard.collect_campaigns(options.agentsLog, active_pys, options.debug)
condor_jobs = dashboard.collect_condor_jobs(options.schedds, options.debug)
catalog_lag = dashboard.collect_catalog_lag(options.checkfileDb, debug=options.debug)

campaigns = dashboard.merge_health(campaigns, condor_jobs, catalog_lag, hb_health)

tree = {
    'generated_at': int(time.time()),
    'heartbeat': {'age_s': hb_age, 'health': hb_health},
    'campaigns': campaigns,
    'agents': dashboard.collect_agents(options.agentsLog),
    'catalog_lag': catalog_lag,
}

dashboard.write_status_json(tree, options.out)

if options.debug > 0:
    print(" Wrote status.json (%d campaigns) --> %s" % (len(campaigns), options.out))
