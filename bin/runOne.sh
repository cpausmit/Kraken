mkdir -p ~/tmp
cd ~/tmp

export CONFIG=nanoao
export VERSION=524
export PY=nano
export DSET=BdToEMu_SoftQCD_TuneCP5_13TeV-pythia8-evtgen+RunIISummer20UL18MiniAODv2-Custom_RDStarPU_BParking_106X_upgrade2018_realistic_v16_L1v1-v2+MINIAODSIM
export DSET=BsToEMu_SoftQCD_TuneCP5_13TeV-pythia8-evtgen+RunIISummer20UL18MiniAODv2-Custom_RDStarPU_BParking_106X_upgrade2018_realistic_v16_L1v1-v2+MINIAODSIM
#export DSET=InclusiveDileptonMinBias_TuneCP5Plus_13p6TeV_pythia8+Run3Summer22MiniAODv3-Pilot_124X_mcRun3_2022_realistic_v12-v4+MINIAODSIM
#export DSET=InclusiveDileptonMinBias_TuneCP5Plus_13p6TeV_pythia8+Run3Summer22MiniAODv3-Pilot_124X_mcRun3_2022_realistic_v12-v5+MINIAODSIM
#export FILE=00123de1-f3f9-42ce-a7c3-d5472c28e7ac

mkdir -p ~/tmp/$CONFIG/$VERSION

cp ~/Tools/Kraken/bin/commonKraken.sh ~/tmp/$CONFIG/$VERSION
cp ~/Tools/Kraken/bin/releaseKraken.sh ~/tmp/$CONFIG/$VERSION

cp /tmp/x509up_u5410 ~/cms/cmssw/$VERSION/CMSSW*/kraken*tgz ~/cms/jobs/lfns/$DSET.lfns ~/tmp/$CONFIG/$VERSION
cd ~/tmp/$CONFIG/$VERSION

if [ -z $FILE ]
then
  FILE=`head -9  $DSET.lfns | tail -1 | cut -d ' ' -f2`
fi
GPACK=`basename $FILE | sed 's/.root//'`

source ./commonKraken.sh
conditions $DSET
./releaseKraken.sh cmsRun $CONFIG $VERSION $PY $DSET $GPACK $FILE tmp_0_0
