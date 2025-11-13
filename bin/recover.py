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
    #print(f" INFO - running: {cmd}")
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
    request_ids = {}
    for request in requests:
        if not opts.dataset:
            dsets.append(f"{request[0]}+{request[1]}+{request[2]}")
            request_ids[f"{request[0]}+{request[1]}+{request[2]}"] = int(request[8])
        else:
            if opts.dataset in f"{request[0]}+{request[1]}+{request[2]}":
                dsets.append(f"{request[0]}+{request[1]}+{request[2]}")
                request_ids[f"{request[0]}+{request[1]}+{request[2]}"] = int(request[8])
                
    return dsets,request_ids

def get_files_from_request(request_id):
    """
    collect all files fro a given request_id
    """
    files = []

    # Access the database to determine all requests
    db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
    cursor = db.cursor()
    sql = "select FileName from Files where RequestId=%d"%(request_id)
    
    if debug:
        print(' SQL: ' + sql)
    
    # Try to access the database
    try:
        # Execute the SQL command
        cursor.execute(sql)
        results = cursor.fetchall()
    except:
        print(" Error (%s): unable to fetch data."%(sql))
        sys.exit(0)

    for result in results:
        files.append(result[0])
        
    return files

def remove_file_from_db(request_id,file):
    # remove a missing file from the database

    # Access the database to remove a given file
    db = MySQLdb.connect(read_default_file="/home/tier3/cmsprod/.my.cnf",read_default_group="mysql",db="Bambu")
    cursor = db.cursor()
    sql = "delete from Files where RequestId=%d and fileName='%s'"%(request_id,file)

    if debug:
        print(' SQL: ' + sql)
    
    try:
        # execute the SQL command
        print(" Deleting: %s"%(file))
        cursor.execute(sql)
    except:
        print(" Error (%s): unable to delete data."%(sql))

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

def process_dataset(dset,request_id,opts):
    """
    Processing a dataset means several failures will be fixed
    a) files that are on disk but not in the database will be newly cataloged
    b) files that are in the database but not on disk will be reproduced
    """

    print(f" #=-=-=-=- DATASET: {dset} =-=-=-=-=-")
    ds_path = f"/cms/store/user/paus/{opts.config}/{opts.version}/{dset}"

    # List root files
    lines = list_remote(ds_path)
    files = [cols[1] for l in lines if 'root' in l and (cols := l.split()) and len(cols) >= 2]
    files_dict = {}
    for l in lines:
        cols = l.split()
        if 'root' in l and len(cols) >= 2:
            lfn = (cols[1].split("/")[8]).replace(".root","")
            files_dict[lfn] = cols[1]
    print(f" Found {len(files_dict)} root files on disk")
    
    # Find database entries
    files_in_db = get_files_from_request(request_id)
    print(f" Found {len(files_in_db)} files in db")

    # Remove database entries that do not have a corresponding file on disk
    if len(files_dict) > 0:
        for f_db in files_in_db:
            if f_db not in files_dict:
                remove_file_from_db(request_id,f_db)
    
    # Add database entries for files on disk that do not have one (we will catalog those files again)
    recover_db_entries = []
    for file in files_dict:
        if file not in files_in_db:
            recover_db_entries.append(files_dict[file])

    # Prepare the persistent check list
    check_list = Path('checkFile.list')
    if check_list.exists():
        check_list.unlink()
    check_list.touch()

    for file in recover_db_entries:
        check_list.write_text(check_list.read_text() + file + "\n")
#        
#    
#    # by default we do not recover
#    
#    # Filter files not in catalog
#    catalog_dir = Path(f"/home/tier3/cmsprod/catalog/t2mit/{opts.config}/{opts.version}/{dset}/Files")
#    for file in files:
#        if file.startswith('#'):
#            continue
#        fid = Path(file).parts[8] if len(Path(file).parts) > 8 else None
#        in_catalog = False
#        if catalog_dir.exists():
#            content = catalog_dir.read_text().splitlines()
#            in_catalog = any(fid and fid in line for line in content)
#        if not in_catalog:
#            do_recovery = True
#            print(f" {fid} processing")
#            check_list.write_text(check_list.read_text() + file + "\n")

    # Update FIBS if needed
    if len(recover_db_entries)>0:
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
            f"--pattern {dset} --displayOnly 1", capture_output=True, shell=True
        )    

def main():
    opts = parse_arguments()

    dsets_disk = make_dataset_list(opts)
    dsets_db,request_ids = get_all_requests(opts)

    for dset in dsets_disk:
        if dset not in dsets_db:
            print(f" ERROR -- Dataset: {dset} not in DB")
            print(f" addRequest.py --config {opts.config} --version {opts.version} --py {opts.py} --dataset {dset}")
    for dset in dsets_db:
        if dset not in dsets_disk:
            print(f" WARNING -- Dataset: {dset} not on disk")
    
    # Process each dataset
    for dset in dsets_disk:
        if dset in dsets_db:
            process_dataset(dset,request_ids[dset],opts)

    # Final web synchronization
    if not opts.fast:
        run_cmd("synchronizeWeb.py", shell=True)

if __name__ == '__main__':
    main()
