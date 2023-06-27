#----------------------------------------------------------------------------------------------------
#  U S E F U L   V A R I A B L E S
#----------------------------------------------------------------------------------------------------
export NTHREADS=$KRAKEN_CONDOR_NCPUS
if [ ".$NTHREADS" == "." ]
then
  echo " WARNING - KRAKEN_CONDOR_NCPUS is not set. Use 2 threads."
  export NTHREADS=2
fi
#----------------------------------------------------------------------------------------------------
#  U S E F U L   F U N C T I O N S
#----------------------------------------------------------------------------------------------------
#
# info on era and conditions are summarized at:
#     https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/Releases/NanoAODv9
#
function customise {
  # provide string for the customise command

  # read command line parameters
  version="$1"

  if   [ "$version" == "501" ]
  then
      echo "PhysicsTools/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  elif [ "$version" == "502" ] || [ "$version" == "503" ] || [ "$version" == "504" ] || [ "$version" == "505" ] || [ "$version" == "506" ] 
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  elif [ "$version" == "507" ] || [ "$version" == "508" ] || [ "$version" == "509" ] || [ "$version" == "510" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  elif [ "$version" == "511" ] || [ "$version" == "512" ] || [ "$version" == "513" ] || [ "$version" == "514" ] || [ "$version" == "515" ] || [ "$version" == "516" ] || [ "$version" == "517" ] || [ "$version" == "518" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBmmMuonId \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  elif [ "$version" == "519" ] || [ "$version" == "520" ]
  then
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeDileptonPlusX --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBmmMuonId \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  elif [ "$version" == "521" ] || [ "$version" == "522" ] || [ "$version" == "523" ]
  then
      echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeDileptonPlusX --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBmmMuonId \
            --customise PhysicsTools/NanoAOD/V10/nano_cff.nanoAOD_customizeV10 \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  elif [ "$version" == "A00" ] || [ "$version" == "A01" ] || [ "$version" == "A02" ]
  then
    echo "PhysicsTools/SUEPNano/nano_suep_cff.SUEPNano_customize \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  elif [ "$version" == "D00" ] || [ "$version" == "D01" ] || [ "$version" == "D02" ]
  then
    echo "Hrare/NanoAOD/nano_cff.nanoAOD_customizeMesons \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  else
    echo "Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBxToMuMu --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeV0ForMuonFake --customise=Bmm5/NanoAOD/nano_cff.nanoAOD_customizeBmmMuonId \
            --customise_commands=\"process.add_(cms.Service('InitRootHandlers',EnableIMT=cms.untracked.bool(False)))\""
  fi
}

function era {
  # provide string for the era given a dataset to process

  # read command line parameters
  dataset=`echo $1 |sed -e 's#^/##' -e 's#/#+#'`
  cmssw="$2"

  #if [  "`echo $cmssw | grep ^12_`" != "" ]
  #then
  #  echo NOT USED
  #  return
  #fi
  
  ## -DATA- STARTS HERE

  if   [ "`echo $dataset | grep +Run2016`" != "" ]
  then
    if   [ "`echo $dataset | grep _HIPM_UL2016`" != "" ]
    then
      echo Run2_2016_HIPM,run2_nanoAOD_106Xv2
    elif [ "`echo $dataset | grep _UL2016`" != "" ]
    then
      echo Run2_2016,run2_nanoAOD_106Xv2
    else
      echo Run2_2016,run2_nanoAOD_94X2016
    fi
  elif [ "`echo $dataset | grep +Run2017`" != "" ]
  then
    if [ "`echo $dataset | grep _UL2017`" != "" ]
    then
      echo Run2_2017,run2_nanoAOD_106Xv2
    else
      echo Run2_2017,run2_nanoAOD_94XMiniAODv2
    fi
  elif [ "`echo $dataset | grep +Run2018`" != "" ]
  then
    if   [ "`echo $dataset | grep UL2017`" != "" ]
    then
      echo Run2_2018,run2_nanoAOD_106Xv2
    elif [ "`echo $dataset | grep UL2018`" != "" ]
    then
      echo Run2_2018,run2_nanoAOD_106Xv2
    fi
  elif  [ "`echo $dataset | grep +Run2022`" != "" ]
  then
    echo Run3
  
  ## --MC-- STARTS HERE
  #  GJets_HT-600ToInf_TuneCP5_13TeV-madgraphMLM-pythia8+RunIISummer20UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1+NANOAODSIM
  elif [ "`echo $dataset | grep +RunIISummer..UL16....AODv2`" != "" ]
  then
    echo Run2_2016,run2_nanoAOD_106Xv2
  elif [ "`echo $dataset | grep +RunIISummer..UL16....AOD`" != "" ]
  then
    echo Run2_2016,run2_nanoAOD_106Xv1
  elif [ "`echo $dataset | grep +RunIISummer..UL17....AODv2`" != "" ]
  then
    echo Run2_2017,run2_nanoAOD_106Xv2
  elif [ "`echo $dataset | grep +RunIISummer..UL17....AOD`" != "" ]
  then
    echo Run2_2017,run2_nanoAOD_106Xv1
  elif [ "`echo $dataset | grep +RunIISummer..UL18....AODv2`" != "" ]
  then
    echo Run2_2018,run2_nanoAOD_106Xv2
  elif [ "`echo $dataset | grep +RunIISummer..UL18....AOD`" != "" ]
  then
    echo Run2_2018,run2_nanoAOD_106Xv1
  
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
  elif  [ "`echo $dataset | grep +Run3Summer22`" != "" ]
  then
    echo Run3
  else
    echo UNKNOWN
  fi
}

function conditions {
  # provide string for the conditions given a dataset to process

  # read command line parameters
  dataset=`echo $1 |sed -e 's#^/##' -e 's#/#+#'`
  cmssw="$2"

  if [  "`echo $cmssw | grep ^12_`" != "" ]
  then
    echo auto:run2_data
    return
  fi
  
  ## -DATA- STARTS HERE
  if   [ "`echo $dataset | grep +Run2016`" != "" ]
  then
    if [ "`echo $dataset | grep UL2016`" != "" ]
    then
      echo 106X_dataRun2_v35
    else	
      echo 102X_dataRun2_v12
    fi
  elif [ "`echo $dataset | grep +Run2017`" != "" ]
  then
    if   [ "`echo $dataset | grep 09Aug2019_UL2017`" != "" ]
    then
      echo 106X_dataRun2_v20
    elif [ "`echo $dataset | grep UL2017`" != "" ]
    then
      echo 106X_dataRun2_v35
    else
      echo 102X_dataRun2_v12
    fi
  elif [ "`echo $dataset | grep +Run2018[A-C]`" != "" ]
  then
    if [ "`echo $dataset | grep UL2018`" != "" ]
    then
      echo 106X_dataRun2_v35
    else
      echo 102X_dataRun2_v12
    fi
  elif [ "`echo $dataset | grep +Run2018D`" != "" ]
  then
    if [ "`echo $dataset | grep UL2018`" != "" ]
    then
      echo 106X_dataRun2_v35
    else
      echo 102X_dataRun2_Prompt_v15
    fi
  elif  [ "`echo $dataset | grep +Run2022`" != "" ]
  then
    echo 124X_dataRun3_Prompt_v4
  
  # --MC-- STARTS HERE
  elif [ "`echo $dataset | grep +RunIISummer..UL16....AODAPV`" != "" ]
  then
    echo 106X_mcRun2_asymptotic_preVFP_v11
  elif [ "`echo $dataset | grep +RunIISummer..UL16....AOD`" != "" ]
  then
    echo 106X_mcRun2_asymptotic_v17
  elif [ "`echo $dataset | grep +RunIISummer..UL17....AOD`" != "" ]
  then
    echo 106X_mc2017_realistic_v9
  elif [ "`echo $dataset | grep +RunIISummer..UL18....AOD`" != "" ]
  then
    echo 106X_upgrade2018_realistic_v16_L1v1
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
  elif  [ "`echo $dataset | grep +Run3Summer22`" != "" ]
  then
    echo 124X_mcRun3_2022_realistic_postEE_v1
  else
    echo UNKNOWN
  fi
}

function showAds {
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

  serverList="cmsxrootd.fnal.gov cms-xrd-global.cern.ch xrootd.unl.edu"
  #serverList="cms-xrd-global.cern.ch"

  # in case this is private MIT Tier-2 data
  if [ "`echo $lfn | grep store/user/paus`" != "" ]
  then
    serverList="xrootd.cmsaf.mit.edu xrootd1.cmsaf.mit.edu xrootd10.cmsaf.mit.edu "
    voms-proxy-info -all
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
  
      echo " Execute:  xrdcp -s root://$server/$lfn ./$gpack.root"
      xrdcp -s root://$server/$lfn ./$gpack.root
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
  echo " submitted from: $SUBMIT_HOSTNAME"
  echo ""
}  

function initialState {
  # provide a summary of where we are when we start the job

  iniState $*
  echo ""
  echo " HOME:" ~/
  echo " "
  cat /proc/cpuinfo | grep -i flags | sort -u
  #env | sort -u
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
  # - this will use the present working directory to do this

  THIS_CMSSW_VERSION="$1"
  PWD=`pwd`
  echo ""
  echo "============================================================"
  echo " Initialize CMSSW $THIS_CMSSW_VERSION"
  # this is the best way to do it but el8 builds are not on Tier3
  #SCRAM_ARCH=`grep CMSSW_$THIS_CMSSW_VERSION /cvmfs/cms.cern.ch/releases.map|grep prodarch=1|cut -d \; -f1|sed 's/architecture=//'`
  # not perfect but will avoid not having the right release
  SCRAM_ARCH=`tar fzt $BASEDIR/kraken_$THIS_CMSSW_VERSION.tgz | grep ^lib/| cut -d / -f2|tail -1`
  echo " -- SCRAM_ARCH: $SCRAM_ARCH"
  scram project CMSSW CMSSW_$THIS_CMSSW_VERSION
  pwd
  ls -lhrt
  ls -lhrt CMSSW_$THIS_CMSSW_VERSION/lib
  cd CMSSW_$THIS_CMSSW_VERSION/src 
  echo " setting CMSSW environment"
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
  if [ ".`echo $BASEDIR | grep $USER`" == "." ]
  then
    batch=1
  fi
  return $batch
}
