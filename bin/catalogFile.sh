#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Catalog exactly one file, either interactively or submitting to batch system.
#
#                                                                             Ch.Paus (Dec 09, 2008)
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

export CATALOG_MACRO="runSimpleFileCataloger.C"

dataDir=$1
dataFile=$2
if [ ".$2" == "." ]
then
  dataFile=`basename $dataDir`
  dataDir=`dirname $dataDir`
fi

procId=$$
logFile=`echo $dataFile.$$ | tr '/' '+'`
logFile=/tmp/$logFile

echo " Initialize CMSSW"; echo " "
source /cvmfs/cms.cern.ch/cmsset_default.sh
dir=`scram list|grep CMSSW|grep -v pre| head -2| grep cvmfs | tr -s ' ' |cut -d ' ' -f3`
# old ? #dir=`scram list -a|grep CMSSW| head -2| grep cvmfs | tr -s ' ' |cut -d ' ' -f3`
cd     $dir/src
eval   `scram runtime -sh`
cd -   >& /dev/null

# show the certificate
if [ -e "./x509up_u`id -u`" ]
then
  export X509_USER_PROXY="./x509up_u`id -u`"
fi
echo " INFO -- using the x509 ticket: $X509_USER_PROXY"
echo " Time left: "`voms-proxy-info -timeleft`" seconds."

# Get ready to run
rm -f $logFile
echo "" `which root`
echo " "; echo " Starting root now"; echo " "
echo " root -l -b -q $KRAKEN_BASE/root/${CATALOG_MACRO}($dataDir,$dataFile >& $logFile"
root -l -b -q -n $KRAKEN_BASE/root/${CATALOG_MACRO}\(\"$dataDir\",\"$dataFile\"\) >& $logFile
  
status=`echo $?`
error=`cat $logFile |grep -v mithep::Selector::UpdateRunInfo | grep -v 'no dictionary for class' | grep 'Error' | wc -l`
zip=`grep R__unzip: $logFile | wc -l`
  
echo " "
echo "Status: $status  Errors: $error  R__Unzip: $zip"
if [ $status == 0 ] && [ $error == 0 ] && [ $zip == 0 ]
then
  cat $logFile
  echo "DECISION"
  echo "  File  $dataDir/$dataFile  looks healthy, make entry into cataloging database."
  echo " "
  echo -n " XX-CATALOG-XX "
  cat $logFile | grep ^0000
else
  echo " ==== DUMPING LOGFILE NOW ===="
  cat $logFile
  echo "DECISION"
  echo "  File  $dataDir/$dataFile  looks corrupted, remove it."
fi

echo "rm -f $logFile"
rm -f $logFile

exit 0
