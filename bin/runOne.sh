mkdir -p ~/tmp
cd ~/tmp

export CONFIG=nanohr
export VERSION=D02
export PY=nano
##export DSET=ScoutingPFHT+Run2018C-v1+RAW
##export DSET=QCD_HT700to1000_TuneCP5_13TeV-madgraphMLM-pythia8+RunIISummer20UL17RECO-106X_mc2017_realistic_v6-v2+AODSIM 

export DSET=Tau+Run2018B-UL2018_MiniAODv2-v2+MINIAOD
#export FILE=

mkdir -p ~/tmp/$CONFIG/$VERSION

cp ~/Tools/Kraken/bin/releaseKraken.sh ~/tmp/$CONFIG/$VERSION

cp /tmp/x509up_u5410 ~/cms/cmssw/$VERSION/CMSSW*/kraken*tgz ~/cms/jobs/lfns/$DSET.lfns    ~/tmp/$CONFIG/$VERSION
cd ~/tmp/$CONFIG/$VERSION

if [ -z $FILE ]
then
  FILE=`head -100  $DSET.lfns | tail -1 | cut -d ' ' -f2`
fi
GPACK=`basename $FILE | sed 's/.root//'`

./releaseKraken.sh cmsRun $CONFIG $VERSION $PY $DSET $GPACK $FILE tmp_0_0
