#!/bin/bash
# --------------------------------------------------------------------------------------------------
#
# Test script for a new Kraken release.
#
# --------------------------------------------------------------------------------------------------

# make a test directory
mkdir tmp_kraken
cd    tmp_kraken

# find config
CONFIG=nanoao
VERSION=507
PY=nano
DATASET=Charmonium+Run2016B-17Jul2018_ver1-v1+MINIAOD

# copy lfns and tar ball
scp t3serv015.mit.edu:cms/jobs/lfns/${DATASET}.lfns .
TGZ=`ls -hrt ~/cms/cmssw/$VERSION/CMSSW*/kraken*tgz | tail -1`
cp $TGZ .

# find first file
INPUT_FILE=`head -1 ${DATASET}.lfns | cut -d' ' -f2`
IFILE=`basename $INPUT_FILE | sed 's/.root$//'`

# start
EXECUTE="releaseKraken.sh cmsRun $CONFIG $VERSION $PY $DATASET $IFILE $INPUT_FILE tmp_test"
echo $EXECUTE
$EXECUTE
