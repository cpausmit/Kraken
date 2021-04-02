#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Catalog a given directory of files of private MC.
#
#                                                                             Ch.Paus (Jan 26, 2021)
#---------------------------------------------------------------------------------------------------
# some basic printing
h=`basename $0`
echo " "
echo " Script:    $h"
echo " Arguments: ($*)"
echo " "
echo " start time    : "`date`
echo " user executing: "`whoami`" --> "`id`
echo " running on    : "`/bin/hostname`
echo " executing in  : "`pwd`
echo " ";

export CATALOG_TRUNC=/home/cmsprod/catalog/t2mit/mc
export CATALOG_MACRO="runSimpleFileCataloger.C"

dataDir=$1
TIER=`basename $dataDir`; tmp=`dirname $dataDir`
SETUP=`basename $tmp`;    tmp=`dirname $tmp`
PROCESS=`basename $tmp`

# make a list of file to process
ls -1 $dataDir | sed "s#^#$dataDir/#" > tmp_list.txt
#cat tmp_list.txt


logFile=`echo $dataDir.$$ | tr '/' '+'`
logFile=/tmp/$logFile
echo " root -l -b -q $KRAKEN_BASE/root/${CATALOG_MACRO}($dataDir,"") >& $logFile"
root -l -b -q -n $KRAKEN_BASE/root/${CATALOG_MACRO}\(\"$dataDir\",\"\"\) >& $logFile

#logFile=test.tmp

echo "Catalog: $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER"
mkdir -p $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER
grep CATALOG $logFile |cut -d ' ' -f 3-10 > $CATALOG_TRUNC/$PROCESS/$SETUP/$TIER/RawFiles.00

rm -f $logFile

exit 0