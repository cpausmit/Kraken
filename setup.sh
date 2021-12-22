# Where does stuff come from

myRoot=/home/submit/paus
pkgRoot=/home/submit/paus/Tools

# Other packages needed
source $pkgRoot/Dools/setup.sh
source $pkgRoot/FiBS/setup.sh
source $pkgRoot/T2Tools/setup.sh paus paus

# Kraken parameters (edit as needed)

# for the agents
export KRAKEN_USER=paus
export KRAKEN_GROUP=zh

export KRAKEN_BASE=$pkgRoot/Kraken
export KRAKEN_ACTIVITY=ecce
export KRAKEN_WORK=$myRoot/$KRAKEN_ACTIVITY/jobs
export KRAKEN_INIT=/cvmfs/eic.opensciencegrid.org/ecce/gcc-8.3/opt/fun4all/core/bin/ecce_setup.sh
export KRAKEN_SCRIPT=runEcce.sh
export KRAKEN_EXE=root
export KRAKEN_SW=$myRoot/$KRAKEN_ACTIVITY/eccesw
export KRAKEN_REMOTE_USER=paus           # user for submit (can be different from Tier-3)

export KRAKEN_SE_BASE=/cms/store/user/paus
export KRAKEN_CATALOG_INPUT=/home/submit/paus/catalog/t2mit
export KRAKEN_CATALOG_OUTPUT=/home/submit/paus/catalog/t2mit
export KRAKEN_TMP_PREFIX='tmp_0_'
export KRAKEN_CONDOR_REQ=""             # overwrite only to fix the requirement (not recommended)
export KRAKEN_ERROR_DB=$KRAKEN_BASE/config/heldErrors.db

export PATH=${PATH}:${KRAKEN_BASE}/bin
export PYTHONPATH=${PYTHONPATH}:${KRAKEN_BASE}/python
