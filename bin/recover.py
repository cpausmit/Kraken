#!/usr/bin/env python
"""
recover.py --config <config> --version <version> --py <py> [--dataset <dataset>] [--fast]

Example:
    recover.py --config nanoao --version 532 --py nano --dataset XYZ+SETUP+MINI --fast

"""
import sys
import subprocess
import MySQLdb
from pathlib import Path
from optparse import OptionParser

debug = 0

def run_cmd(cmd, capture_output=False, shell=False):
    """Run a command. If capture_output is True, return stdout as text."""
    if capture_output:
        return subprocess.check_output(cmd, shell=shell, text=True)
    return subprocess.call(cmd, shell=shell)

def list_remote(path):
    """Run 'list' on a remote path and return its output lines."""
    try:
        out = run_cmd(f"list {path}", capture_output=True, shell=True)
        return out.splitlines()
    except subprocess.CalledProcessError as e:
        print(f" Error listing {path}: {e}", file=sys.stderr)
        return []

def parse_arguments():
    usage = "usage: %prog --config CONF --version VERS --py PY [--dataset DSET] [--fast]"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--config", dest="config",help="configuration name (required)")
    parser.add_option("-v", "--version", dest="version",help="version identifier (required)")
    parser.add_option("-p", "--py", dest="py",help="Python script name (required)")
    parser.add_option("-d", "--dataset", dest="dataset",help="dataset pattern to process (optional)")
    parser.add_option("-f", "--fast", dest="fast",action="store_true",default=False,help="skip catalog generation and web sync (optional)")
    options, args = parser.parse_args()
    if not options.config or not options.version or not options.py:
        parser.error("--config, --version and --py are required arguments")
    return options

def get_all_requests(opts):
    """
    collect all datasets matching this set of (config,version,py), no further selection yet
    """
    config = opts.config
    version = opts.version
    py = opts.py

    # Access the database to determine all requests
    db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
    cursor = db.cursor()
    sql = 'select ' + \
        'Datasets.DatasetProcess,Datasets.DatasetSetup,Datasets.DatasetTier,'+\
        'Datasets.DatasetDbsInstance,Datasets.DatasetNFiles,' + \
        'RequestConfig,RequestVersion,RequestPy,RequestId,RequestNFilesDone from Requests ' + \
        'left join Datasets on Requests.DatasetId = Datasets.DatasetId '+ \
        'where RequestConfig="' + config + '" and RequestVersion = "' + version + \
        '" and RequestPy = "' + py + \
        '" order by Datasets.DatasetProcess, Datasets.DatasetSetup, Datasets.DatasetTier;'

    if debug:
        print(' SQL: ' + sql)
    
    # Try to access the database
    try:
        # Execute the SQL command
        cursor.execute(sql)
        requests = cursor.fetchall()      
    except:
        print(" Error (%s): unable to fetch data."%(sql))
        sys.exit(0)
        
    dsets = []
    for request in requests:
        dsets.append(f"{request[0]}+{request[1]}+{request[2]}")
        
    return dsets

def make_dataset_list(opts):
    # Determine the list of datasets
    base = f"/cms/store/user/paus/{opts.config}/{opts.version}"
    if not opts.dataset:
        print(f" OK -- recovering: {opts.config} {opts.version} {opts.py}")
        lines = list_remote(base)
    else:
        print(f" OK -- recovering: {opts.config} {opts.version} {opts.py} *{opts.dataset}*")
        lines = list_remote(f"{base}/*{opts.dataset}*")

    if any("ERROR on remote end: 1" in l for l in lines):
        print(" no matching datasets. EXIT!")
        sys.exit(1)
    dsets = sorted({parts[7] for l in lines if (parts := l.strip().split('/')) and len(parts) >= 8 and parts[7]})

    return dsets
        
def process_dataset(dset,opts):
    print(f" #=-=-=-=- DATASET: {dset} =-=-=-=-=-")
    ds_path = f"/cms/store/user/paus/{opts.config}/{opts.version}/{dset}"

    # List root files
    lines = list_remote(ds_path)
    files = [cols[1] for l in lines if 'root' in l and (cols := l.split()) and len(cols) >= 2]
    print(f" Found {len(files)} root files")

    # Write temporary list file
    tmp_file = Path('checkFile-tmp.list')
    tmp_file.write_text("".join(f + "\n" for f in files if not f.startswith('#')))

    # Prepare the persistent check list
    check_list = Path('checkFile.list')
    if check_list.exists():
        check_list.unlink()
    check_list.touch()

    # by default we do not recover
    do_recovery = False
    
    # Filter files not in catalog
    catalog_dir = Path(f"/home/tier3/cmsprod/catalog/t2mit/{opts.config}/{opts.version}/{dset}/Files")
    for file in files:
        if file.startswith('#'):
            continue
        fid = Path(file).parts[8] if len(Path(file).parts) > 8 else None
        in_catalog = False
        if catalog_dir.exists():
            content = catalog_dir.read_text().splitlines()
            in_catalog = any(fid and fid in line for line in content)
        if not in_catalog:
            do_recovery = True
            print(f" {fid} processing")
            check_list.write_text(check_list.read_text() + file + "\n")

    # Update FIBS if needed
    if do_recovery:
        fibs_cmd = (
            "cat /home/tier3/cmsprod/cms/work/fibs/checkFile.list checkFile.list "
            "| sort -u > /tmp/new.list; mv /tmp/new.list /home/tier3/cmsprod/cms/work/fibs/checkFile.list"
        )
        run_cmd(f"fibsLock.py --config checkFile --cmd \"{fibs_cmd}\"", shell=True)
        run_cmd("kickCatalog -q", shell=True)

    # If not fast, generate catalogs and update web
    if not opts.fast:
        run_cmd(f"generateCatalogs.py {opts.config}/{opts.version} {dset}", shell=True)
        run_cmd(
            f"reviewRequests.py --config {opts.config} --version {opts.version} --py {opts.py} "
            f"--pattern {dset} --displayOnly 1", shell=True
        )    

def main():
    opts = parse_arguments()

    dsets_disk = make_dataset_list(opts)
    #print(" DATASETS:")
    #for dset in dsets_disk:
    #    print(f" {dset}")
    dsets_db = get_all_requests(opts)

    for dset in dsets_disk:
        if dset not in dsets_db:
            print(f" ERROR -- Dataset: {dset} not in DB")
            print(f" addRequest.py --config {opts.config} --version {opts.version} --py {opts.py} --dataset {dset}")
    for dset in dsets_db:
        if dset not in dsets_disk:
            print(f" WARNING -- Dataset: {dset} not on disk")
    
    # Process each dataset
    for dset in dsets_disk:
        process_dataset(dset,opts)
        
    # Final web synchronization
    if not opts.fast:
        run_cmd("synchronizeWeb.py", shell=True)

if __name__ == '__main__':
    main()
