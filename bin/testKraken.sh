#!/bin/bash
# --------------------------------------------------------------------------------------------------
#
# Test script for a new Kraken release.
#
# --------------------------------------------------------------------------------------------------

# make a test directory
mkdir -p tmp_kraken
cd    tmp_kraken

# find config
CONFIG=nanoao
VERSION=510
PY=nano
DATASET=MET+Run2016B-17Jul2018_ver1-v1+MINIAOD
##      Charmonium+Run2016B-17Jul2018_ver1-v1+MINIAOD

# copy lfns and tar ball
scp t3serv019.mit.edu:/home/cmsprod/cms/jobs/lfns/${DATASET}.lfns .
TGZ=`ssh t3serv019.mit.edu ls -hrt /home/cmsprod/cms/cmssw/$VERSION/CMSSW*/kraken*tgz | tail -1`
scp t3serv019.mit.edu:$TGZ .
scp cmsprod@t3serv019.mit.edu:/tmp/x509up_u5410 ./
export X509_USER_PROXY=/tmp/x509up_u5410 

# find first file
INPUT_FILE=`head -1 ${DATASET}.lfns | cut -d' ' -f2`
IFILE=`basename $INPUT_FILE | sed 's/.root$//'`

# start
EXECUTE="releaseKraken.sh cmsRun $CONFIG $VERSION $PY $DATASET $IFILE $INPUT_FILE tmp_test"
echo $EXECUTE
$EXECUTE
