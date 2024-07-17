# source /cvmfs/cms.cern.ch/cmsset_default.sh
# cmssw-cc7
# export PS1="[\[\033[1;31m\]\$(date +%H:%M)-CS7-\[\033[1;30m\]\u@\h:\[\033[1;32m\]\w\[\033[0m\]] "

# make sure to be in centos 7

mkdir -p ~/tmp
cd ~/tmp

export CONFIG=nanoao
export VERSION=529
export PY=nano
export DSET=DstarToD0Pi_D0ToKPi_KPiToMuMu_KPiLifetime0p1_SoftQCDnonD_TuneCP5_13p6TeV_pythia8-evtgen+Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v2+MINIAODSIM
#ZeroBias+Run2022C-PromptReco-v1+MINIAOD
#export FILE=5804156f-e3b8-45a1-bac7-542b1536ec75
#c3684755-30f3-4089-b8c2-97157f933cfa

# just for the dark photon scouting data
export KRAKEN_CONDOR_NCPUS="2"

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
