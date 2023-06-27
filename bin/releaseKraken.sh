#!/bin/bash
#===================================================================================================
#
# Execute one job on the grid or interactively.
#
#===================================================================================================
if [ "." == ".$*" ]
then
  echo " No work to do. EXIT"
  return
fi

# load our tools
echo " Load Kraken functions."
ls -l
if [ -f "./commonKraken.sh" ]
then
  source ./commonKraken.sh
else
  source commonKraken.sh    
fi

#---------------------------------------------------------------------------------------------------
#  M A I N   S T A R T S   H E R E
#---------------------------------------------------------------------------------------------------
echo " START -- "`date +%s`
echo ""
echo " Executing: $0 $* "

# make sure we are locked and loaded
export BASEDIR=`pwd`
echo " Executing: $0 $* "

# set ourselves into the work directory from here on
mkdir ./work
export WORKDIR=`pwd`/work
export HOME=$WORKDIR  # this might be an issue with root
cd $WORKDIR

# command line arguments with examples
EXE="$1"        # cmsRun
CONFIG="$2"     # nanoao -- pandaf
VERSION="$3"    # 500    -- 002
PY="$4"	        # nano   -- data-03feb2017
TASK="$5"       # MET+Run2016B-03Feb2017_ver2-v2+MINIAOD
GPACK="$6"      # 6EBC0286-34EE-E611-832F-0025905B8600
LFN="$7"        # /store/data/Run2016B/ ... /6EBC0286-34EE-E611-832F-0025905B8600.root
TMP_PREFIX="$8" # tmp_0_170302_132124                               

# load all parameters relevant to this task
echo " Initialize package"
test=`ls $BASEDIR/kraken_*tgz 2> /dev/null`
if [ ".$test" == "." ]
then
  echo ' ERROR - Kraken tar ball is missing. No point to continue.'
  echo " END -- "`date +%s`
  exit 1
fi
cmsswVersion=`echo $BASEDIR/kraken_*.tgz | sed -e 's@.*kraken_@@' -e 's@.tgz@@'`

# Derive essential paramters from command line parameters
era=`era $TASK $cmsswVersion`
conditions=`conditions $TASK $cmsswVersion`
customise=`customise $VERSION $cmsswVersion`
echo ""
echo " Dataset:    $TASK"
echo " Era:        $era"
echo " Conditions: $conditions"
echo " Customize:  $customise"
echo ""
if [ ".$8" == ".TEST" ]
then
  exit 0
fi

# get some variables for monitoring
host=`hostname`
book=$CONFIG/$VERSION
args_hash=`echo $LFN | md5sum |cut -d' ' -f1`

# define base output location
REMOTE_SERVER="se01.cmsaf.mit.edu"
REMOTE_BASE="/cms/store"
REMOTE_USER_DIR="/user/paus/$CONFIG/$VERSION"
REMOTE_SERVER_XRD="xrootd.cmsaf.mit.edu"
REMOTE_BASE_XRD="/store"


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

if [ "`echo $TASK | grep AODSIM`" != "" ]
then
  isMC="isMC=1"
else
  isMC="isMC=0"
fi

if [ ${PY} == "nano" ]
then
  isMC=""
  if [ "`echo $TASK | grep AODSIM`" != "" ]
  then
    echo "\
    cmsDriver.py step1 --step NANO --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --mc --eventcontent NANOAODSIM --datatier NANOAODSIM \
      --era $era --conditions $conditions --customise=$customise \
         "
    cmsDriver.py step1 --step NANO --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --mc --eventcontent NANOAODSIM --datatier NANOAODSIM \
      --era $era --conditions $conditions --customise=$customise
  else
    echo "\
    cmsDriver.py step1 --step NANO --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --data --eventcontent NANOAOD --datatier NANOAOD \
      --era $era --conditions $conditions --customise=$customise \
        "
    cmsDriver.py step1 --step NANO --number=-1 --no_exec --python_filename $WORKDIR/nano.py \
      --filein file:${GPACK}.root \
      --fileout file:kraken_000.root \
      --data --eventcontent NANOAOD --datatier NANOAOD \
      --era $era --conditions $conditions --customise=$customise
  fi
elif [ ${PY} == "nanodp" ]
then
  echo " MW production"
  cat $CMSSW_BASE/$CONFIG/$VERSION/${PY}.py \
      | sed -e "s@XX-LFN-XX@$LFN@g" -e "s@XX-GPACK-XX@$GPACK@g" \
      > $WORKDIR/${PY}.py
elif [ ${PY} == "nanomw" ]
then
  echo " MW production"
  cat $CMSSW_BASE/$CONFIG/$VERSION/${PY}.py \
      | sed -e "s@XX-LFN-XX@$LFN@g" -e "s@XX-GPACK-XX@$GPACK@g" \
      > $WORKDIR/${PY}.py
elif [ ${PY} == "nanosc" ]
then
  echo " SUEP Scouting production"
  cat $CMSSW_BASE/$CONFIG/$VERSION/${PY}.py \
      | sed -e "s@XX-LFN-XX@$LFN@g" -e "s@XX-GPACK-XX@$GPACK@g" \
	    > $WORKDIR/${PY}.py
  ADD=""
  if [ "`echo $LFN | grep UL16`" != "" ]
  then
    ADD="era=2016"
  fi
else
  isMC=""
  # prepare the python config from the given templates
  cat $CMSSW_BASE/$CONFIG/$VERSION/${PY}.py \
      | sed -e "s@XX-LFN-XX@$LFN@g" -e "s@XX-GPACK-XX@$GPACK@g" \
      > $WORKDIR/${PY}.py
fi

# see whether the last process---making the .py file---was succesful
rc="$?"
if [ ".$rc" == ".0" ]
then
  echo " INFO - last call worked: (rc=$rc)"
else
  echo " INFO - last call failed: (rc=$rc)"
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
  echo " List libraries in $CMSSW_BASE/lib"
  ls -l $CMSSW_BASE/lib
  echo " LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
  echo " Exe: \
  $EXE -j $BASEDIR/${GPACK}.empty --numThreads $NTHREADS ${PY}.py $ADD $isMC inputFiles="`cat ./inputFiles | tr "\n" "," | sed 's/,$//'`" outputFile=kraken_000.root" 
  $EXE -j $BASEDIR/${GPACK}.empty --numThreads $NTHREADS ${PY}.py $ADD $isMC inputFiles=`cat ./inputFiles | tr "\n" "," | sed 's/,$//'` outputFile=kraken_000.root
fi

rc=$?

pwd
ls -lhrt

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

sample=`echo $GPACK | sed 's/\(.*\)_nev.*/\1/'`

# unset CMS environment
eval `scram unsetenv -sh`

# setup gfal tools
GFAL_BASE=/cvmfs/grid.cern.ch/centos7-ui-4.0.3-1_umd4v3/etc/profile.d
echo " setting up gfal-copy"
echo "\
source   $GFAL_BASE/setup-c7-ui-example.sh"
source   $GFAL_BASE/setup-c7-ui-example.sh
ls -lhrt $GFAL_BASE
which gfal-copy

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
  if [ ".$rcCmsCp" != ".0" ]
  then
    # removing remainders
    echo "Remove file remainders:\
    gfal-rm gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}"
    gfal-rm gsiftp://$REMOTE_SERVER:2811/${REMOTE_BASE}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}
    rcSrmRm=$?
    echo " Remove RC: $rcSrmRm"
    # now do the backup copy using xrootd
    echo " Try again:\
    xrdcp file:///$pwd/${file} \
          root://$REMOTE_SERVER_XRD/${REMOTE_BASE_XRD}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}"
    xrdcp file:///$pwd/${file} \
          root://$REMOTE_SERVER_XRD/${REMOTE_BASE_XRD}${REMOTE_USER_DIR}/${TASK}/${TMP_PREFIX}/${file}
    rcCmsCp=$?
    echo " ReCopying: $file"
    echo " ReCopy RC: $rcCmsCp"
  fi
done

# make condor happy because it also might want some of the files
executeCmd mv $WORKDIR/*.root $BASEDIR/

# leave the worker super clean
testBatch
if [ ".$?" == ".1" ]
then
  cd $BASEDIR
  executeCmd rm -rf $WORKDIR *.root
fi

# create the pickup output file for condor (this is needed to make sure failing jobs go to hold in condor)
echo " ---- D O N E ---- $host " >> $BASEDIR/${GPACK}.empty

pwd
ls -lhrt

echo " ---- Cleaning up log file ----"
if [ -e "_condor_stderr" ]
then
  echo "\
  cat _condor_stderr | grep -v Begin > tmp"
  cat _condor_stderr | grep -v Begin > tmp
  mv tmp _condor_stderr
fi

pwd
ls -lhrt
echo " ---- D O N E ----"

echo " END -- "`date +%s`
exit 0
