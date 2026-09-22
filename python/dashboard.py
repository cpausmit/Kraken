#---------------------------------------------------------------------------------------------------
# Python Module File to collect Kraken production status into a single JSON tree for the
# all-Python monitoring dashboard (agents/dashboard/). Read-only: this module only ever reads
# from the DB/condor/filesystem, it never mutates production state.
#
# Author: C.Paus                                                                      (Sep 01, 2026)
#---------------------------------------------------------------------------------------------------
import os, sys, json, time, subprocess

import kdb
import jsum

# health severity, low to high -- used to roll a health up from samples to versions to configs
HEALTH_ORDER = ['ok', 'warn', 'held', 'stale', 'dead', 'unknown']

def worse(a, b):
    # return the more severe of two health strings
    ia = HEALTH_ORDER.index(a) if a in HEALTH_ORDER else HEALTH_ORDER.index('unknown')
    ib = HEALTH_ORDER.index(b) if b in HEALTH_ORDER else HEALTH_ORDER.index('unknown')
    return a if ia >= ib else b

#---------------------------------------------------------------------------------------------------
def heartbeat_health(path, warn_s=900, dead_s=3600):
    # heartbeat file is just touched with `date` every cycle by synchronizeWeb.py
    if not os.path.exists(path):
        return ('unknown', -1)

    age = int(time.time() - os.path.getmtime(path))
    if age > dead_s:
        return ('dead', age)
    if age > warn_s:
        return ('stale', age)
    return ('ok', age)

#---------------------------------------------------------------------------------------------------
def parse_review_cycle(cycle_cfg):
    # KRAKEN_REVIEW_CYCLE is frequently just "=$KRAKEN_CLEANUP_CYCLE" (a shell variable
    # reference), so this has to actually source the file like the old index.php's
    # `shell_exec('source cycle.cfg; echo $KRAKEN_REVIEW_CYCLE')` did, not hand-parse it.
    # Returns the set of "config:version:py" tokens that are considered "active".
    active = set()
    if not os.path.exists(cycle_cfg):
        return active

    cmd = 'source %s; echo "$KRAKEN_REVIEW_CYCLE"' % (cycle_cfg)
    try:
        out = subprocess.check_output(cmd, shell=True, executable='/bin/bash').decode()
    except Exception:
        return active

    for reqset in out.split():
        f3 = reqset.split(':')
        if len(f3) != 3:
            continue
        config, version, pys = f3
        for py in pys.split(','):
            active.add('%s:%s:%s' % (config, version, py))

    return active

#---------------------------------------------------------------------------------------------------
def discover_plots(dir):
    # list PNGs already produced by progress.py/analyzeCatalog.py, most recent first
    if not os.path.isdir(dir):
        return []
    names = [n for n in os.listdir(dir) if n.endswith('.png')]
    names.sort(key=lambda n: os.path.getmtime(os.path.join(dir, n)), reverse=True)
    return names

def discover_logs(dir, limit=5):
    # list the most recent *.log files, matching the old index.php-Template `ls -t *.log | head -5`
    if not os.path.isdir(dir):
        return []
    names = [n for n in os.listdir(dir) if n.endswith('.log')]
    names.sort(key=lambda n: os.path.getmtime(os.path.join(dir, n)), reverse=True)
    return names[:limit]

def discover_files(dir, names):
    # keep only the names that actually exist in dir (README, ncounts.err, status-<py>, ...)
    if not os.path.isdir(dir):
        return []
    return [n for n in names if os.path.exists(os.path.join(dir, n))]

#---------------------------------------------------------------------------------------------------
def collect_condor_jobs(schedds, debug=0):
    # bucket every queued/running/held job by (config,version,py,dataset), keyed off the
    # "Arguments" ClassAd built by task.py's writeCondorSubmit():
    #   "<exe> <config> <version>  <py> <dataset> $(GPACK) $(FILE) <tag>"
    #
    # Kraken submits through more than one scheduler (see reviewRequests.py's
    # setupSchedulers(): the local host as cmsprod, and KRAKEN_CONDOR_SCHEDD as
    # KRAKEN_REMOTE_USER), so this queries every schedd given and merges the results.
    jobs = {}

    for schedd in schedds:
        for (jobStatus, args) in _query_condor(schedd, debug):
            f = args.split()
            if len(f) < 5:
                continue
            config, version, py, dataset = f[1], f[2], f[3], f[4]
            key = (config, version, py, dataset)
            if key not in jobs:
                jobs[key] = jsum.Jsum()
            jobs[key].add_job(jobStatus, 0)

    return jobs

def _query_condor(schedd, debug=0):
    # prefer the htcondor python bindings; fall back to the condor_q CLI in JSON mode
    try:
        import htcondor
        collector = htcondor.Collector()
        ads = collector.locate(htcondor.DaemonTypes.Schedd, schedd)
        schedd_obj = htcondor.Schedd(ads)
        rows = []
        for ad in schedd_obj.query(projection=['JobStatus', 'Args']):
            rows.append((int(ad.get('JobStatus', 0)), str(ad.get('Args', ''))))
        return rows
    except Exception as ex:
        if debug > 0:
            print(' INFO - htcondor bindings unavailable for %s (%s), falling back to condor_q -json' % (schedd, ex))

    cmd = 'condor_q -name %s -json 2> /dev/null' % (schedd)
    try:
        out = subprocess.check_output(cmd, shell=True).decode()
        ads = json.loads(out) if out.strip() else []
    except Exception as ex:
        print(' ERROR - condor_q fallback failed for %s (%s)' % (schedd, ex))
        return []

    rows = []
    for ad in ads:
        rows.append((int(ad.get('JobStatus', 0)), str(ad.get('Args', ''))))
    return rows

#---------------------------------------------------------------------------------------------------
def collect_campaigns(agents_log, active_pys, debug=0):
    # walk $KRAKEN_AGENTS_LOG/reviewd/<config>/<version>/ the same way index.php used to scan it,
    # and pull the authoritative per-sample counts from the DB instead of scraping rendered text
    campaigns = {}
    reviewd = os.path.join(agents_log, 'reviewd')
    if not os.path.isdir(reviewd):
        return campaigns

    db = kdb.Kdb(debug)

    for config in sorted(os.listdir(reviewd)):
        config_dir = os.path.join(reviewd, config)
        if not os.path.isdir(config_dir):
            continue

        for version in sorted(os.listdir(config_dir)):
            version_dir = os.path.join(config_dir, version)
            if not os.path.isdir(version_dir):
                continue

            pys = set()
            for name in os.listdir(version_dir):
                if name.startswith('status-') and not name.endswith('.html'):
                    pys.add(name[len('status-'):])

            samples = {}
            for row in db.find_requests(config, version):
                (process, setup, tier, dbs, nFiles, rConfig, rVersion, rPy, rId, nFilesDone) = row
                if process is None:
                    continue
                dataset = '%s+%s+%s' % (process, setup, tier)
                sample_dir = os.path.join(version_dir, dataset)
                n_total = int(nFiles) if nFiles is not None else 0
                n_done = int(nFilesDone) if nFilesDone is not None and int(nFilesDone) >= 0 else 0

                samples[dataset] = {
                    'id': '%s/%s/%s' % (config, version, dataset),
                    'py': rPy,
                    'n_total': n_total,
                    'n_done': n_done,
                    'n_nocatalog': max(n_total - n_done, 0),
                    'n_batch': 0, 'n_idle': 0, 'n_running': 0, 'n_held': 0,
                    'plots': discover_plots(sample_dir),
                    'readme': discover_files(sample_dir, ['README']),
                    'ncounts_err': discover_files(sample_dir, ['ncounts.err']),
                }
                pys.add(rPy)

            campaigns.setdefault(config, {})[version] = {
                'id': '%s/%s' % (config, version),
                'pys': {py: ('%s:%s:%s' % (config, version, py)) in active_pys for py in sorted(pys)},
                'samples': samples,
                'plots': discover_plots(version_dir),
                'status_files': discover_files(version_dir, ['status-%s' % py for py in pys]),
                'incomplete_files': discover_files(version_dir, ['incomplete-%s' % py for py in pys]),
                'queue_file': discover_files(version_dir, ['queue']),
            }

    return campaigns

#---------------------------------------------------------------------------------------------------
def collect_catalog_lag(db_path, tail_bytes=20 * 1024 * 1024, debug=0):
    # checkFileActivity.db lines look like "config:version:dataset:file,status:stime:etime:size"
    # (atom.Atom.summary()); tail the file instead of reading the whole (~120MB) thing every cycle
    lag = {}
    if not os.path.exists(db_path):
        return lag

    size = os.path.getsize(db_path)
    with open(db_path, 'r', errors='ignore') as f:
        if size > tail_bytes:
            f.seek(size - tail_bytes)
            f.readline()  # drop the partial first line
        for line in f:
            if ',' not in line:
                continue
            key, value = line.strip().split(',', 1)
            kf = key.split(':')
            vf = value.split(':')
            if len(kf) < 2 or len(vf) < 3:
                continue
            config, version = kf[0], kf[1]
            try:
                etime = int(vf[2])
            except ValueError:
                continue
            mkey = '%s:%s' % (config, version)
            if mkey not in lag or etime > lag[mkey]:
                lag[mkey] = etime

    now = int(time.time())
    return {k: {'age_s': now - v} for k, v in lag.items()}

#---------------------------------------------------------------------------------------------------
def collect_agents(agents_log, agent_names=('catalogd', 'cleanupd', 'monitord', 'reviewd')):
    # top-level per-daemon area: plots and recent logs sitting directly in $KRAKEN_AGENTS_LOG/<agent>/
    agents = {}
    for name in agent_names:
        agent_dir = os.path.join(agents_log, name)
        agents[name] = {
            'plots': discover_plots(agent_dir),
            'logs': discover_logs(agent_dir),
        }
    return agents

#---------------------------------------------------------------------------------------------------
def _sample_health(sample):
    if sample['n_held'] > 0:
        return 'held'
    if sample['n_total'] > 0 and sample['n_done'] >= sample['n_total']:
        return 'ok'
    if sample['n_batch'] > 0 or sample['n_idle'] > 0 or sample['n_running'] > 0:
        return 'warn'
    if sample['n_nocatalog'] > 0:
        return 'warn'
    return 'ok'

def merge_health(campaigns, condor_jobs, catalog_lag, heartbeat, catalog_warn_s=3600, catalog_dead_s=14400):
    # fold condor job counts and catalog lag into the campaign tree, and compute one
    # health enum per sample/version/config
    for config, versions in campaigns.items():
        for version, vnode in versions.items():
            v_health = 'ok'

            for dataset, sample in vnode['samples'].items():
                key = (config, version, sample['py'], dataset)
                js = condor_jobs.get(key)
                if js is not None:
                    sample['n_batch'] = int(js.n_batch)
                    sample['n_idle'] = int(js.n_idle)
                    sample['n_running'] = int(js.n_running)
                    sample['n_held'] = int(js.n_held)

                sample['health'] = _sample_health(sample)
                v_health = worse(v_health, sample['health'])

            lag = catalog_lag.get('%s:%s' % (config, version))
            if lag is not None:
                age = lag['age_s']
                if age > catalog_dead_s:
                    v_health = worse(v_health, 'dead')
                elif age > catalog_warn_s:
                    v_health = worse(v_health, 'stale')
                vnode['catalog_lag_s'] = age
            else:
                vnode['catalog_lag_s'] = None

            vnode['health'] = v_health
            vnode['active'] = any(vnode['pys'].values())

    return campaigns

#---------------------------------------------------------------------------------------------------
def write_status_json(tree, out_path):
    # atomic write so the JS polling loop never fetches a half-written file mid-rsync
    tmp_path = out_path + '.tmp'
    with open(tmp_path, 'w') as f:
        json.dump(tree, f, indent=1, sort_keys=True)
    os.rename(tmp_path, out_path)
    return
