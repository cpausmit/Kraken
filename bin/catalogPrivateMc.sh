#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Catalog a given directory of files of private MC by creating a catalog file:
#
# usage:
# ex. catalogPrivateMc.sh \
#                   /cms/store/user/paus/mc/SUEP-m125-generic-htcut/RunIIAutumn18-private/MINIAODSIM
# 
# input: directory of files to catalog
# ex. /cms/store/user/paus/mc/SUEP-m125-generic-htcut/RunIIAutumn18-private/MINIAODSIM
#
# output: 
# ex. ~cmsprod/catalog/t2mit/mc/SUEP-m125-generic-htcut/RunIIAutumn18-private/MINIAODSIM/RawFiles.00
#
#                                                                             Ch.Paus (Jan 26, 2021)
#---------------------------------------------------------------------------------------------------
# some basic printing
h=`basename $0`
export CATALOG_TRUNC=/home/tier3/cmsprod/catalog/t2mit/mc
export CATALOG_MACRO="runSimpleFileCataloger.C"
dataDir=$1

TIER=`basename $dataDir`; tmp=`dirname $dataDir`
SETUP=`basename $tmp`;    tmp=`dirname $tmp`
PROCESS=`basename $tmp`

echo " "
echo " Script:    $h"
echo " Arguments: ($*)"
echo " "
echo " start time    : "`date`
echo " user executing: "`whoami`" --> "`id`
echo " running on    : "`/bin/hostname`
echo " executing in  : "`pwd`
echo " ";
echo " catalog       : $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER"

# make a list of file to process
list $dataDir | cut -d ' ' -f2 > tmp_list.txt

##ls -1 $dataDir | sed "s#^#$dataDir/#" > tmp_list.txt
#cat tmp_list.txt

logFile=`echo $dataDir.$$ | tr '/' '+'`
logFile=/tmp/$logFile
echo " root -l -b -q $KRAKEN_BASE/root/${CATALOG_MACRO}($dataDir,"") >& $logFile"
root -l -b -q -n $KRAKEN_BASE/root/${CATALOG_MACRO}\(\"$dataDir\",\"\"\) | tee >& $logFile

echo "Catalog: $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER"
mkdir -p $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER
grep CATALOG $logFile |cut -d ' ' -f 3-10 > $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER/RawFiles.00

rm -f $logFile

# # here you can explicitely make lfns and jobs files but it is not needed or recommended
# # simply use: addDataset.py --dataset /mc/$PROCESS/$SETUP/$TIER
#
# generateLfns.py -r $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER/RawFiles.00  \
#   > ~/cms/jobs/lfns/$PROCESS+$SETUP+$TIER.lfns
# generateLfns.py -r $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER/RawFiles.00 -j \
#   > ~/cms/jobs/jobs/$PROCESS+$SETUP+$TIER.jobs
#

exit 0
