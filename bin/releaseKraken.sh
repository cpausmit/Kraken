#!/bin/bash
#===================================================================================================
#
# Execute one job on the grid or interactively.
#
#===================================================================================================

#----------------------------------------------------------------------------------------------------
#  U S E F U L   F U N C T I O N S
#----------------------------------------------------------------------------------------------------
function customise {
  # provide string for the customise command

  # read command line parameters
  version="$1"

  if [ "$version" == "501" ]
  then
    echo "PhysicsTools/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu"
  elif [ "$version" == "502" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu"
  elif [ "$version" == "503" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu"
  elif [ "$version" == "504" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu"
  elif [ "$version" == "505" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu"
  elif [ "$version" == "506" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu"
  elif [ "$version" == "507" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake"
  elif [ "$version" == "508" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake"
  elif [ "$version" == "509" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake"
  elif [ "$version" == "510" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake"
  elif [ "$version" == "A00" ]
  then
    echo "PhysicsTools/SUEPNano/nano_suep_cff.SUEPNano_customize"
  else
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBmmMuonId"
  fi
}

function era {
  # provide string for the era

  # read command line parameters
  dataset="$1"

  #echo ERA : $dataset
  ## +RunIISpring16
  ## +RunIISummer17
  
  if   [ "`echo $dataset | grep +RunIISummer19UL17`" != "" ]
  then
    echo Run2_2017,run2_nanoAOD_106Xv1
  elif [ "`echo $dataset | grep +Run2016`" != "" ]
  then
    echo Run2_2016,run2_nanoAOD_94X2016
  elif [ "`echo $dataset | grep +Run2017`" != "" ]
  then
    if [ "`echo $dataset | grep 09Aug2019_UL2017`" != "" ]
    then
      echo Run2_2017,run2_nanoAOD_106Xv1
    else
      echo Run2_2017,run2_nanoAOD_94XMiniAODv2
    fi
  elif [ "`echo $dataset | grep +Run2018`" != "" ]
  then
    echo Run2_2018,run2_nanoAOD_102Xv1
  elif [ "`echo $dataset | grep +RunIISummer16`" != "" ]
  then
    if [ "`echo $dataset | grep MiniAODv2`" != "" ]
    then
      echo Run2_2016,run2_miniAOD_80XLegacy
    else
      echo Run2_2016,run2_nanoAOD_94X2016
    fi
  elif [ "`echo $dataset | grep +RunIIFall17`" != "" ]
  then
    echo Run2_2017,run2_nanoAOD_94XMiniAODv2
  elif [ "`echo $dataset | grep +RunIIAutumn18`" != "" ]
  then
    echo Run2_2018,run2_nanoAOD_102Xv1
  elif [ "`echo $dataset | grep SUEP`" != "" ]
  then
    echo Run2_2018,run2_nanoAOD_102Xv1
  else
    echo UNKNOWN
  fi
}

function conditions {
  # provide string for the conditions

  # read command line parameters
  dataset="$1"
  #echo CONDITIONS : $dataset

  if   [ "`echo $dataset | grep +RunIISummer19UL17`" != "" ]
  then
    echo 106X_dataRun2_v20
  elif [ "`echo $dataset | grep +Run2016`" != "" ]
  then
    echo 102X_dataRun2_v12
  elif [ "`echo $dataset | grep +Run2017`" != "" ]
  then
    if [ "`echo $dataset | grep 09Aug2019_UL2017`" != "" ]
    then
      echo 106X_dataRun2_v20
    else
      echo 102X_dataRun2_v12
    fi
  elif [ "`echo $dataset | grep +Run2018[A-C]`" != "" ]
  then
    echo 102X_dataRun2_v12
  elif [ "`echo $dataset | grep +Run2018D`" != "" ]
  then
    echo 102X_dataRun2_Prompt_v15
  elif [ "`echo $dataset | grep +RunIISummer16`" != "" ]
  then
    if [ "`echo $dataset | grep MiniAODv2`" != "" ]
    then
      echo 94X_mcRun2_asymptotic_v2
    else
      echo 102X_mcRun2_asymptotic_v7
    fi
  elif [ "`echo $dataset | grep +RunIIFall17`" != "" ]
  then
    echo 102X_mc2017_realistic_v7
  elif [ "`echo $dataset | grep +RunIIAutumn18`" != "" ]
  then
    echo 102X_upgrade2018_realistic_v20
  elif [ "`echo $dataset | grep SUEP`" != "" ]
  then
    echo 102X_upgrade2018_realistic_v20
  else
    echo UNKNOWN
  fi
}

function exeCmd {
  # provide a small frame for each command, also allows further steering
  echo " Executing: $*"
  $*
}  

function executeCmd {
  # provide a nice frame for each command, also allows further steering

  echo " "
  echo " =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
  exeCmd $*
  echo " Completed: $*"
  echo " =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
  echo " "
  
}  

function configureSite {
  # in case we are not at a CMS site we need to have a configuration
  #
  # -- ATTENTION -- CMSSW has to be setup before calling configure site
  #

  # get the certificates
  echo "---- Setup certificates ----"
  #CERTS_DIR="/etc/grid-security/certificates"
  CERTS_DIR="/cvmfs/cms.cern.ch/grid/etc/grid-security/certificates"
  if ! [ -d "$CERTS_DIR" ] 
  then
    CERTS_DIR="/cvmfs/oasis.opensciencegrid.org/osg-software/osg-wn-client/3.2/current/el6-x86_64/etc/grid-security/certificates"
    echo "Using OSG location at: $CERTS_DIR"
  else
    echo "Using CMS certificates: $CERTS_DIR"
  fi
  export X509_CERT_DIR=$CERTS_DIR
  export X509_USER_PROXY=`echo $BASEDIR/x509up_*`
  env | grep X509

  link="/cvmfs/cms.cern.ch/SITECONF/local"
  if ! [ -e "$link" ]                          # recover other setups
  then
    echo " Link does not exist: $link."
    echo " - try IN2P3: /etc/cvmfs/SITECONF/T1_VO_CMS_SW_DIR/SITECONF/local"
    link="/etc/cvmfs/SITECONF/T1_VO_CMS_SW_DIR/SITECONF/local"
    if ! [ -e "$link" ]                       # recover other setups
    then
      echo " ERROR  -- config does not exist locally"
    fi
  fi
  xml="$link/JobConfig/site-local-config.xml"

  echo "---- Setup SiteConfig ----"
  echo " Link       = $link"
  echo " Xml        = $xml"
  echo " CMSSW_BASE = $CMSSW_BASE"

  if [ -e "$xml" ]
  then
    echo " Config exists: $xml."
    return
  else
    echo " ERROR -- config does not exist: $xml"
  fi

  ls -lh $CMSSW_BASE/tgz/siteconf.tgz
  echo "  -- unpacking private local config to recover"
  executeCmd tar fzx $CMSSW_BASE/tgz/siteconf.tgz
  cd SITECONF
  rm -f local
  testGeoId=`curl -s http://cmsopsquid.cern.ch/wpad.dat | grep 'Bad Request'`
  if [ "$testGeoId" == "" ]
  then
    ln -s ./T3_US_OSG ./local
  else
    ln -s ./T2_US_MIT ./local
  fi

  ls -lhrt
  cd -
  # make sure this is the config to be used
  export CMS_PATH=`pwd`
}

function downloadFiles {
  # find all input files and loop through to 

  # read command line parameters
  task="$1"
  gpack="$2"
  lfn="$3"

  echo " "
  echo " Downloading all input files: $task $gpack $lfn"
  echo " ============================"
  #cat $BASEDIR/$task.lfns

  # grep the input files belonging to this job
  echo " INPUTS:  grep $gpack $BASEDIR/$task.lfns | cut -d' ' -f2"
  if [ ${#gpack} == "36" ]
  then
    inputLfns=`grep $gpack $BASEDIR/$task.lfns | cut -d' ' -f2`
  elif [ ${#gpack} == "4" ]
  then
    inputLfns=`grep ^$gpack $BASEDIR/$task.lfns | cut -d' ' -f2`
  else
    inputLfns=`grep $gpack.root $BASEDIR/$task.lfns | cut -d' ' -f2`
  #else
  #  echo " ERROR -- unexpected GPACK: $gpack"
  #  echo " END -- "`date +%s`
  #  exit 253
  fi
  echo " Input LFNs: $inputLfns"
  echo " "
  echo " VOMS-PROXY-INFO "
  voms-proxy-info -all
  cd $WORKDIR; pwd; ls -lhrt

  rm -rf ./inputFiles
  touch  ./inputFiles

  for lfn in $inputLfns
  do
    fileId=`basename $lfn | sed 's/.root//'`
    downloadFile $fileId $lfn
    if ! [ -e "./$fileId.root" ]
    then
      echo " EXIT(255) -- download failed."
      echo " END -- "`date +%s`
      exit 255
    fi

    # add this file to the input list
    echo " GPACK #gpack: ${#gpack} "
    if   [ ${#gpack} == "4" ]
    then
      echo "$fileId.root" >> ./inputFiles
    elif [ ${#gpack} == "36" ]
    then
      echo "file:$fileId.root" >> ./inputFiles
    fi
  done

  echo " =========================="
  echo "  Input files for this job "
  echo " =========================="
  cat ./inputFiles
}

function downloadFile {
  # download one given lfn using xrootd

  # read command line parameters
  gpack="$1"
  lfn="$2"

  if [ -e "$lfn" ]; then
    echo " File exists locally: $lfn"
    ln -s $lfn
  fi

  #serverList="cms-xrd-global.cern.ch cmsxrootd.fnal.gov xrootd.unl.edu"
  serverList="cms-xrd-global.cern.ch"

  # in case this is private MIT Tier-2 data
  if [ "`echo $lfn | grep store/user/paus`" != "" ]
  then
    serverList="xrootd.cmsaf.mit.edu xrootd1.cmsaf.mit.edu xrootd10.cmsaf.mit.edu "
  fi

  echo ""
  echo " Make local copy of the root file with LFN: $lfn"

  if [ -e "./$gpack.root" ]
  then
    echo " File exists already locally: ./$gpack.root"
  else
    for server in $serverList
    do
      echo " Trying server: $server at "`date`
  
      echo " Execute:  xrdcp -d 1 -s root://$server/$lfn ./$gpack.root"
      xrdcp -d 1 -s root://$server/$lfn ./$gpack.root
      rc="$?"
  
      if [ "$rc" != "0" ]
      then
        echo " ERROR -- Copy command failed (potential leftovers deleted) -- RC: $rc at "`date`
        rm -f ./$gpack.root
      fi
  
      if [ -e "./$gpack.root" ]
      then
        echo " Looks like copy worked on server: $server at "`date`
        break
      else
        echo " ERROR -- ./$gpack.root does not exist or corrupt (RC:$rc, server:$server at "`date`")"
      fi
    done
  fi

  if [ -e "./$gpack.root" ]
  then
    ls -lhrt ./$gpack.root
  else
    echo " ERROR -- input file ./$gpack.root does not exist. Failed on all servers: $serverList"
    echo "          EXIT now because there is no AOD* file to process."
    return
  fi
}  

function iniState {
  # provide a short summary of where we are when we start the job

  h=`basename $0`
  echo "Script:    $h"
  echo "Arguments: $*"
  
  # some basic printing
  echo " "
  echo "${h}: Show who and where we are"
  echo " start time    : "`date`
  echo " user executing: "`id`
  echo " running on    : "`hostname`
  echo " uname -a      : "`uname -a`
  echo " executing in  : "`pwd`
  echo " submitted from: $HOSTNAME"
  echo ""
}  

function initialState {
  # provide a summary of where we are when we start the job

  iniState $*
  echo ""
  echo " HOME:" ~/
  echo " "
  cat /proc/cpuinfo | grep -i flags | sort -u
  env | sort -u
  ls -lhrta
  showDiskSpace
}

function haveCvmfs {
  # check whether we have CVMFS available on the node

  echo ""
  echo " Checking CVMFS "
  echo " ============== "
  source /cvmfs/cms.cern.ch/cmsset_default.sh
  if [ ".$?" == ".0" ]
  then
    echo " -> cvmfs found: /cvmfs/cms.cern.ch/cmsset_default.sh"
  else
    echo " ERROR : cvmfs not found: ls -lhrt /"
    ls -lhrt /
    ls -lhrt /cvmfs
    df /cvmfs
    echo ""
    echo " CVMFS ads - job"
    grep -i cvmfs $PWD/.job.ad
    echo ""
    echo " CVMFS ads - machine"
    grep -i cvmfs $PWD/.machine.ad
    echo ""
    return 252
  fi
}

function setupCmssw {
  # setup a specific CMSSW release and add the local python path

  THIS_CMSSW_VERSION="$1"
  PWD=`pwd`
  echo ""
  echo "============================================================"
  echo " Initialize CMSSW $THIS_CMSSW_VERSION"
  if     [ "`echo $THIS_CMSSW_VERSION | grep ^8_`" != "" ] \
     ||  [ "`echo $THIS_CMSSW_VERSION | grep ^9_`" != "" ]
  then
    export SCRAM_ARCH=slc6_amd64_gcc530
  fi
  echo " -- SCRAM_ARCH: $SCRAM_ARCH"
  scram project CMSSW CMSSW_$THIS_CMSSW_VERSION
  pwd
  ls -lhrt
  ls -lhrt *
  cd CMSSW_$THIS_CMSSW_VERSION/src 
  eval `scram runtime -sh`
  if [ -e  "$BASEDIR/kraken_$THIS_CMSSW_VERSION.tgz" ]
  then
    cd ..
    tar fzx $BASEDIR/kraken_$THIS_CMSSW_VERSION.tgz
    rm      $BASEDIR/kraken_$THIS_CMSSW_VERSION.tgz  # cleanup is good
  fi

  if [ -d "$WORKDIR/CMSSW_$THIS_CMSSW_VERSION/src/Bmm5" ]
  then
    echo " -- SCRAM: setup - rabit, xgboost"
    ## is needed for SL6 ?!
    ##export LD_PRELOAD=$CMSSW_BASE/external/$SCRAM_ARCH/lib/libxgboost.so
    cd $WORKDIR/CMSSW_$THIS_CMSSW_VERSION/src
    scram setup Bmm5/NanoAOD/external-tools/rabit.xml
    scram setup Bmm5/NanoAOD/external-tools/xgboost.xml
    cd -
  fi

  cd $PWD
  echo "============================================================"
  configureSite
  echo ""
}

function showDiskSpace {
  # implement a simple minded summary of the available disk space and usage

  [ -z $BASEDIR ] && $BASEDIR="./"

  echo ""
  echo " Disk space overview "
  echo " =================== "
  df -h $BASEDIR
  echo ""
  echo " Disk space usage "
  echo " ================ "
  du -sh $BASEDIR/*
}

function testBatch {
  # implement simple minded/not perfect test to see whether script is run in batch

  batch=0
  if [ "`echo $PWD | grep $USER`" == "" ]
  then
    batch=1
  fi
  return $batch
}

#----------------------------------------------------------------------------------------------------
#  M A I N   S T A R T S   H E R E
#----------------------------------------------------------------------------------------------------
echo " START -- "`date +%s`
echo ""
echo " Executing: $0 $* "
echo ""
echo " ============================================================================ "
echo " Job ads in $PWD/.job.ad"
cat $PWD/.job.ad | sort -u
echo ""
echo " ============================================================================ "
echo " Machine ads in $PWD/.machine.ad"
cat $PWD/.machine.ad | sort -u
echo ""
echo " ============================================================================ "
echo ""
echo " ============================================================================ "
echo " Which singularity?"
which singularity

## do we need to move the base directory? [ EAPS ]
#TEST_BASEDIR="/tmp"
#if [ -d "$TEST_BASEDIR" ]
#then
#  DATE=`date +%y%m%d-%H%M%S`
#  # change landing spot
#  mkdir -p $TEST_BASEDIR/${DATE}_${SLURM_NODELIST}_${SLURM_JOB_NAME}
#  cp -r  * $TEST_BASEDIR/${DATE}_${SLURM_NODELIST}_${SLURM_JOB_NAME}
#  cd $TEST_BASEDIR/${DATE}_${SLURM_NODELIST}_${SLURM_JOB_NAME}
#  # show new landing spot
#  echo " -- Changed basedir --"
#  pwd
#  echo " -- Our stuff --"
#  ls -lhrt
#  echo " Back to the normal routine now..."
#fi

# make sure we are locked and loaded
export BASEDIR=`pwd`
echo " Executing: $0 $* "

# command line arguments
                # -- example
EXE="$1"        # cmsRun
CONFIG="$2"     # nanoao -- pandaf
VERSION="$3"    # 500    -- 002
PY="$4"	        # nano   -- data-03feb2017
TASK="$5"       # MET+Run2016B-03Feb2017_ver2-v2+MINIAOD
GPACK="$6"      # 6EBC0286-34EE-E611-832F-0025905B8600
LFN="$7"        # /store/data/Run2016B/ ... /6EBC0286-34EE-E611-832F-0025905B8600.root
TMP_PREFIX="$8" # tmp_0_170302_132124                               

# get some variables for monitoring
host=`hostname`
book=$CONFIG/$VERSION
args_hash=`echo $LFN | md5sum |cut -d' ' -f1`

# load all parameters relevant to this task
echo " Initialize package"
test=`ls kraken_*tgz 2> /dev/null`
if [ "$test" == "" ]
then
  echo ' ERROR - Kraken tar ball is missing. No point to continue.'
  echo " END -- "`date +%s`
  exit 1
fi

cmsswVersion=`echo kraken_*.tgz | sed -e 's@kraken_@@' -e 's@.tgz@@'`

# make sure to contain file mess
mkdir ./work
cd    ./work
export WORKDIR=`pwd`

# this might be an issue with root
export HOME=$WORKDIR

# tell us the initial state
initialState $*

####################################################################################################
# initialize KRAKEN
####################################################################################################

# do we have cvmfs
haveCvmfs
if [ "$?" != "0" ]
then
  echo " ERROR -- crucial CVMFS is not available"
  echo "          EXIT(252) now."
  echo " END -- "`date +%s`
  exit 252
fi

# setting up the software
setupCmssw $cmsswVersion

# download all input files to have them local
downloadFiles $TASK $GPACK $LFN

if [ ${PY} == "nano" ]
then
  era=`era $TASK`
  conditions=`conditions $TASK`
  customise=`customise $VERSION`

  if [ "`echo $TASK | grep AODSIM`" != "" ]
  then

    echo "\
    cmsDriver.py step1 --step NANO --nThreads 2 --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --mc --eventcontent NANOAODSIM --datatier NANOAODSIM \
      --era $era --conditions $conditions --customise=$customise \
      --customise_commands=\"process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)))\"
         "
    cmsDriver.py step1 --step NANO --nThreads 2 --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --mc --eventcontent NANOAODSIM --datatier NANOAODSIM \
      --era $era --conditions $conditions --customise=$customise \
      --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)))"
  else
    echo "\
    cmsDriver.py step1 --step NANO --nThreads 2 --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --data --eventcontent NANOAOD --datatier NANOAOD \
      --era $era --conditions $conditions --customise=$customise \
      --customise_commands=\"process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)))\" \
         "
    cmsDriver.py step1 --step NANO --nThreads 2 --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --data --eventcontent NANOAOD --datatier NANOAOD \
      --era $era --conditions $conditions --customise=$customise \
      --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)))"
  fi
else
  # prepare the python config from the given templates
  cat $CMSSW_BASE/$CONFIG/$VERSION/${PY}.py \
      | sed -e "s@XX-LFN-XX@$LFN@g" -e "s@XX-GPACK-XX@$GPACK@g" \
      > $WORKDIR/${PY}.py
fi

# create the local links
cd $WORKDIR
echo " Preparing links -- $CMSSW_BASE/src/PandaProd/Ntupler/test"
ls -l $CMSSW_BASE/src/PandaProd/Ntupler/test 2> /dev/null
if [ -d "$CMSSW_BASE/src/PandaProd/Ntupler/test/jec" ]
then
  ln -s $CMSSW_BASE/src/PandaProd/Ntupler/test/jec 
fi
if [ -d "$CMSSW_BASE/src/PandaProd/Ntupler/test/jer" ]
then
  ln -s $CMSSW_BASE/src/PandaProd/Ntupler/test/jer 
fi

####################################################################################################
# run KRAKEN
####################################################################################################

# run KRAKEN making
cd $WORKDIR
pwd
ls -lhrt

echo " Exe: python ${PY}.py" 
python ${PY}.py
if [ "$CONFIG" == "testit" ] && [ "$PY" == "test" ]
then
  # very special case to allow more scalable tests
  echo " ---- SUPER QUICK TEST ----"
  echo " ---- SUPER QUICK TEST ----" > kraken_000.root
else
  env; env;
  echo " Exe: \
  $EXE ${PY}.py inputFiles="`cat ./inputFiles | tr "\n" "," | sed 's/,$//'`" outputFile=kraken_000.root" 
  $EXE ${PY}.py inputFiles=`cat ./inputFiles | tr "\n" "," | sed 's/,$//'` outputFile=kraken_000.root
fi

rc=$?

if [ "$rc" != "0" ] 
then
  echo ""
  echo " ERROR -- Return code is not zero: $rc"
  echo "          EXIT, no file copies!!"
  echo ""
  echo " END -- "`date +%s`
  exit $rc
fi

# this is a little naming issue that has to be fixed
mv kraken*.root  ${GPACK}_tmp.root

# cleanup the input
rm -f ./$GPACK.root

if ! [ -e "${GPACK}_tmp.root" ]
then
  echo " ERROR -- kraken production failed. No output file: ${GPACK}_tmp.root"
  echo "          EXIT(254) now because there is no KRAKEN file."
  echo " END -- "`date +%s`
  exit 254
fi

showDiskSpace

####################################################################################################
# push our files out to the Tier-2 / Dropbox
####################################################################################################

cd $WORKDIR
pwd
ls -lhrt

# define base output location
REMOTE_SERVER="se01.cmsaf.mit.edu"
REMOTE_BASE="/cms/store"
REMOTE_USER_DIR="/user/paus/$CONFIG/$VERSION"

sample=`echo $GPACK | sed 's/\(.*\)_nev.*/\1/'`

# unset CMS environment
eval `scram unsetenv -sh`

# setup gfal tools
which gfal-copy
if [ "$?" != "0" ]
then
  echo " setting up gfal-copy"
  source /cvmfs/grid.cern.ch/centos7-ui-test/etc/profile.d/setup-c7-ui-example.sh
  ls -lhrt /cvmfs/grid.cern.ch/centos7-ui-test/etc/profile.d
  which gfal-copy
  #ln -s /cvmfs/singularity.opensciencegrid.org/opensciencegrid/osgvo-el7\:latest/usr/bin $WORKDIR/bin
  #export PATH="$PATH:$WORKDIR/bin"
  #echo " env | grep PATH"
fi

# this is somewhat overkill but works very reliably, I suppose
pwd=`pwd`
for file in `echo ${GPACK}*`
do
  # always first show the proxy and remove the CMSSW environment
  voms-proxy-info -all
  echo " Which gfal-copy are we using? \
  which gfal-copy"
  which gfal-copy
  # now do the copy
  echo "\
  gfal-copy -p file:///$pwd/${file} \
          gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}"
  gfal-copy -p file:///$pwd/${file} \
          gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}
  rcCmsCp=$?
  echo " Copying: $file"
  echo " Copy RC: $rcCmsCp"
  if [ "$rcCmsCp" != "0" ]
  then
    # now do the backup copy
    echo "Remove file remainders:\
    gfal-rm gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}"
    gfal-rm gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}
    rcSrmRm=$?
    echo " Remove RC: $rcSrmRm"
    echo " Try again:\
    gfal-copy file:///$pwd/${file} \
              gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}"
    gfal-copy file:///$pwd/${file} \
              gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}
    rcCmsCp=$?
    echo " ReCopying: $file"
    echo " ReCopy RC: $rcCmsCp"
  fi
done

# make condor happy because it also might want some of the files
executeCmd mv $WORKDIR/*.root $BASEDIR/

# leave the worker super clean
testBatch
if [ "$?" == "1" ]
then
  cd $BASEDIR
  executeCmd rm -rf $WORKDIR *.root
fi

# create the pickup output file for condor (this is needed to make sure failing jobs go to hold in condor)
echo " ---- D O N E ----" > $BASEDIR/${GPACK}.empty

pwd
ls -lhrt

echo " ---- Cleaning up log file ----"
cat _condor_stderr | grep -v Begin > tmp
mv tmp _condor_stderr

pwd
ls -lhrt
echo " ---- D O N E ----"

echo " END -- "`date +%s`
exit 0
