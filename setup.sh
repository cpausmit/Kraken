## Where does stuff come from
#source /cvmfs/grid.cern.ch/etc/profile.d/setup-cvmfs-ui.sh

myRoot=/home/tier3/cmsprod
pkgRoot=/home/tier3/cmsprod/Tools

# Other packages needed
source $pkgRoot/Dools/setup.sh
source $pkgRoot/FiBS/setup.sh
source $pkgRoot/T2Tools/setup.sh paus paus

# Kraken parameters (edit as needed)

# for the agents
export KRAKEN_USER=cmsprod
export KRAKEN_GROUP=submit-cms

export KRAKEN_BASE=$pkgRoot/Kraken
export KRAKEN_ACTIVITY=cms
export KRAKEN_WORK=$myRoot/cms/jobs
export KRAKEN_INIT=/cvmfs/cms.cern.ch/cmsset_default.sh
export KRAKEN_SCRIPT=releaseKraken.sh
export KRAKEN_COMMON=commonKraken.sh
export KRAKEN_SW=$myRoot/$KRAKEN_ACTIVITY/${KRAKEN_ACTIVITY}sw
export KRAKEN_EXE=cmsRun
export KRAKEN_CMSSW=$myRoot/cms/cmssw
export KRAKEN_REMOTE_USER=paus           # user for submit (can be different from Tier-3)

export KRAKEN_SE_BASE=/cms/store/user/paus
export KRAKEN_CATALOG_INPUT=/home/tier3/cmsprod/catalog/t2mit
export KRAKEN_CATALOG_OUTPUT=/home/tier3/cmsprod/catalog/t2mit
export KRAKEN_TMP_PREFIX='tmp_0_'
export KRAKEN_CONDOR_REQ=""              # overwrite only to fix the requirement (not recommended)
export KRAKEN_CONDOR_NCPUS="2"           # can be changed (not recommended)
export KRAKEN_ERROR_DB=$KRAKEN_BASE/config/heldErrors.db

export PATH=${PATH}:${KRAKEN_BASE}/bin
export PYTHONPATH=${PYTHONPATH}:${KRAKEN_BASE}/python
