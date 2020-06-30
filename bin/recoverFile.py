#!/usr/bin/python
# ---------------------------------------------------------------------------------------------------
# Recover a list of files that has been lost on the Tier-2.
#
# v1.0                                                                                  Apr 30, 2019
#---------------------------------------------------------------------------------------------------
import sys,os,subprocess,getopt,time
import MySQLdb
import rex

from lfn import Lfn
from data import Datasets
from data import Dataset
from data import Block

file_list = "missing-g.txt"
# T2_US_MIT_compare_missing.txt"

# ==================================================================================================
# H E L P E R S
# ==================================================================================================

def find_files(dir):
    cmd = "list %s/* "%(dir) + "|grep root"
    myRx = rex.Rex()  
    (rc,out,err) = myRx.executeLocalAction(cmd)

    files = []
    for row in out.split("\n"):
        if len(row) < 2:
            continue
        filename = "/".join((row.split(" ")[-1]).split('/')[-2:])
        files.append(filename)
    
    return files

def find_py(dset_name):
    py = 'mc'
    if 'Run201' in dset_name:
        py = 'data'
        if 'PromptReco' in dset_name:
            py = 'data-2018prompt'

    return py

def make_recovery_lists(data):
    lfns = []
    for line in data.split("\n"):
        f = line.split(" ")
        if len(f) > 0 and f[0].find("/store/user")>-1:
            lfn = Lfn(f[0])
            lfns.append(lfn)
    print " Found %d entries."%(len(lfns))

    datasets = Datasets()
    for lfn in lfns:
        dataset_name = "%s/%s/%s"%(lfn.config,lfn.version,lfn.dataset)
        dataset = datasets.add_dataset(dataset_name)
        # get block and size -- we do not know them but this is not an issues
        block_name = "INVALID"
        file_size = -1
        # add the file
        print " Add LFN: %s"%(lfn.lfn)
        dataset.add_block_file(block_name,lfn.lfn,file_size)

    return datasets

# ==================================================================================================
# M A I N
# ==================================================================================================

# Read the list of files and make a list of datasets
print " Open missing files list: %s"%(file_list)
with open(file_list,"r") as fh:
    data = fh.read()

datasets = make_recovery_lists(data)
#print " "
#datasets.show()

# Go through the list of files and recover
last = ""
files = []
for dataset_name in sorted(datasets.datasets):
    dataset = datasets.datasets[dataset_name]

    book = "/".join(dataset_name.split("/")[0:2])
    if book != last:
        print ' New book (%s), make inventory.'%(book)
        files = find_files("/cms/store/user/paus/%s"%(book))
        print " FILE[0] -- %s"%(files[0])

    print " DATASET recovery: %s"%(dataset.name)
    reprocess = False
    
    for block_name in dataset.blocks:
        block = dataset.blocks[block_name]
        for key in block.sizes:

            # is the file really missing
            mkey = "/".join(key.split("/")[-2:])
            if   mkey in files:
                print " File already exists on Tier2. Do nothing. (%s)"%(mkey)
            # find it on Tier-3
            elif os.path.exists("/mnt/hadoop/cms%s"%(key)):
                print " From T3: %s"%(key)
                cmd = "t2tools.py --action=up --source /mnt/hadoop/cms%s --target /cms%s"%(key,key)
                print " CMD: %s"%(cmd)
                os.system(cmd)
            # lost, so remove from DB and reprocess
            else:
                reprocess = True
                print " Lost: %s"%(key)
                cmd = "removeFile.py --exe --fileName /cms%s"%(key)
                print " CMD: %s"%(cmd)
                os.system(cmd)
        
    if reprocess:
        f = dataset_name.split("/")
        config = f[0]
        version = f[1]
        dset_name = f[2]
        py = find_py(dset_name)

        cmd = " reviewRequests.py --submit --config=%s --version=%s --py=%s --pattern=%s"%(config,version,py,dset_name)
        print " CMD: %s"%(cmd)
        os.system(cmd)

    last = book
