# ALMA 9 OR CENTOS 7?

echo "
 # For CENTOS7 use this
 source /cvmfs/cms.cern.ch/cmsset_default.sh
 cmssw-cc7
 export PS1=\"[\[\033[1;31m\]\$(date +%H:%M)\[\033[1;34m\]-CS7-\[\033[1;30m\]\u@\h:\[\033[1;32m\]\w\[\033[0m\]] \"
 # Otherwise do nothing!

"
mkdir -p ~/tmp
cd ~/tmp

# nanohr D07 nano Muon0+Run2024D-MINIv6NANOv15-v1+MINIAOD 02eeef7b-c85e-4402-aee4-90380e8e3336
export CONFIG=nanoao
export VERSION=535
export PY=nano
export DSET=ParkingDoubleMuonLowMass0+Run2022C-PromptReco-v1+MINIAOD
#ParkingDoubleMuonLowMass0+Run2025C-PromptReco-v1+MINIAOD
#export FILE=02eeef7b-c85e-4402-aee4-90380e8e3336

# just for the dark photon scouting data
export KRAKEN_CONDOR_NCPUS="2"

#export FILE=00123de1-f3f9-42ce-a7c3-d5472c28e7ac

mkdir -p ~/tmp/$CONFIG/$VERSION

cp ~/Tools/Kraken/bin/commonKraken.sh ~/tmp/$CONFIG/$VERSION
cp ~/Tools/Kraken/bin/releaseKraken.sh ~/tmp/$CONFIG/$VERSION

cp /tmp/x509up_u5410 ~/tmp/$CONFIG/$VERSION/x509up_uCMSPROD
cp ~/cms/cmssw/$VERSION/CMSSW*/kraken*tgz ~/cms/jobs/lfns/$DSET.lfns ~/tmp/$CONFIG/$VERSION
cd ~/tmp/$CONFIG/$VERSION

if [ -z $FILE ]
then
  FILE=`head -9  $DSET.lfns | tail -1 | cut -d ' ' -f2`
  echo $FILE
fi
GPACK=`basename $FILE | sed 's/.root//'`


echo " ==== ANALYZING FILE ==== $FILE"

source ./commonKraken.sh
conditions $DSET
./releaseKraken.sh cmsRun $CONFIG $VERSION $PY $DSET $GPACK $FILE tmp_0_0
