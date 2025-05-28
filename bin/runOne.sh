echo "
 source /cvmfs/cms.cern.ch/cmsset_default.sh
 cmssw-cc7
 export PS1=\"[\[\033[1;31m\]\$(date +%H:%M)\[\033[1;34m\]-CS7-\[\033[1;30m\]\u@\h:\[\033[1;32m\]\w\[\033[0m\]] \"
"

# make sure to be in centos 7

mkdir -p ~/tmp
cd ~/tmp

export CONFIG=nanoao
export VERSION=533
export PY=nano
export DSET=K0LToMuMu_K0LFilter_TuneCP5_13p6TeV_pythia8-evtgen+Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v4+MINIAODSIM
#export FILE=

## 106X_dataRun2_v35 	Run2_2018,run2_nanoAOD_106Xv2
## 106X_dataRun2_v35 	Run2_2016,run2_nanoAOD_106Xv2

#K0sToMuMu_K0sFilter_TuneCP5_13p6TeV_pythia8-evtgen+Run3Summer23MiniAODv4-130X_mcRun3_2023_realistic_v15_ext1-v2+MINIAODSIM
#JpsiTo2Mu_JpsiPt8_TuneCP5_13p6TeV_pythia8+Run3Summer22MiniAODv4-MUO_POG_130X_mcRun3_2022_realistic_v5-v2+MINIAODSIM

#export DSET=DoubleMuon+Run2022C-22Sep2023-v1+MINIAOD
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
  echo $FILE
fi
GPACK=`basename $FILE | sed 's/.root//'`


echo " ==== ANALYZING FILE ==== $FILE"

source ./commonKraken.sh
conditions $DSET
./releaseKraken.sh cmsRun $CONFIG $VERSION $PY $DSET $GPACK $FILE tmp_0_0
