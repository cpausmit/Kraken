#!/bin/bash

if [ "." == ".$*" ]
then
    echo " newCampaign.sh <config> <version> <py>"
    echo ""
    echo " No work to do. EXIT"
    exit -1
fi


export CONFIG=$1
export VERSION=$2
export PY=$3

# make directories
mkdir -p $KRAKEN_SW/$VERSION
mkdir -p $KRAKEN_WORK/$CONFIG/$VERSION
mkdir -p $KRAKEN_BASE/$CONFIG/$VERSION

# edit files
emacs $KRAKEN_SW/$VERSION/INSTALL \
      $KRAKEN_BASE/$CONFIG/$VERSION/$PY.py \
      $KRAKEN_BASE/bin/commonKraken.sh \
      $KRAKEN_BASE/bin/releaseKraken.sh

# now build
cd $KRAKEN_SW/$VERSION
source /cvmfs/cms.cern.ch/cmsset_default.sh
cmssw-cc7
# source ./INSTALL
