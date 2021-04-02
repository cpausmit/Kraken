#!/bin/bash
# --------------------------------------------------------------------------------------------------
#
# Installation script for MitProd/Processing/agents. There will be lots of things to test and to
# fix, but this is the starting point. This installation has to be performed as user root.
#
#                                                                Ch.Paus: Version 0.0 (Apr 27, 2015)
# --------------------------------------------------------------------------------------------------

function install {
  # function that will install the daemon named as the given first parameter
  #   example: install reviewd

  # command line parameter
  daemon="$1"
  echo " Installing daemon: $daemon"

  # make sure directories exist
  
  echo " - creating daemon log area: $KRAKEN_AGENTS_LOG/${daemon}"
  mkdir -p $KRAKEN_AGENTS_LOG/${daemon}
  chown ${KRAKEN_USER}:${KRAKEN_GROUP} -R $KRAKEN_AGENTS_LOG

  # stop potentially existing server process
  echo " - stop running daemon"
  if   [ -e "/etc/init.d/${daemon}" ]
  then
    #/etc/init.d/${daemon} status
    /etc/init.d/${daemon} stop
  elif [ -e "/usr/lib/systemd/system/${daemon}.service" ]
  then
    #service ${daemon} status
    service ${daemon} stop
  fi
  
  # copy daemon
  echo " - install daemon as system daemon"
  if [ "0" == "1" ]
  then
    cp $KRAKEN_AGENTS_BASE/sysv/${daemon} /etc/init.d/
  else
    cp $KRAKEN_AGENTS_BASE/systemd/${daemon} /usr/lib/systemd/system/${daemon}.service
    systemctl daemon-reload
  fi
  
  # start new server
  echo " - check and start daemon"
  if [ "0" == "1" ]
  then
    #/etc/init.d/${daemon} status
    /etc/init.d/${daemon} start
    sleep 2
    /etc/init.d/${daemon} status
  else
    #service ${daemon} status
    service ${daemon} start
    sleep 2
    service ${daemon} status
  fi
  
  # start on boot
  echo " - auto restart daemon on boot"
  systemctl enable ${daemon}
  #chkconfig --level 345 ${daemon} on
}

#---------------------------------------------------------------------------------------------------
#                                               M A I N
#---------------------------------------------------------------------------------------------------
BASE="$1"
if [ -z "$BASE" ]
then
  BASE=/home/cmsprod/Tools/Kraken
fi
AGENTS_BASE="$2"
if [ -z "$AGENTS_BASE" ]
then
  AGENTS_BASE=/usr/local/Kraken/agents
fi

# basic installation message
echo ""
echo " Using Kraken base:    $BASE"
echo " Installing agents to: $AGENTS_BASE"
echo ""

# prepare the correct setup.sh file
if [ -f "./setup.sh-Template" ]
then
  cat ./setup.sh-Template \
    | sed -e "s#XX-KRAKEN_BASE-XX#$BASE#" -e "s#XX-KRAKEN_AGENTS_BASE-XX#$AGENTS_BASE#" \
    > ./setup.sh
  cat ./reviewd-Template \
    | sed -e "s#XX-KRAKEN_BASE-XX#$BASE#" -e "s#XX-KRAKEN_AGENTS_BASE-XX#$AGENTS_BASE#" \
    > ./reviewd
  cat ./catalogd-Template \
    | sed -e "s#XX-KRAKEN_BASE-XX#$BASE#" -e "s#XX-KRAKEN_AGENTS_BASE-XX#$AGENTS_BASE#" \
    > ./catalogd
  cat ./cleanupd-Template \
    | sed -e "s#XX-KRAKEN_BASE-XX#$BASE#" -e "s#XX-KRAKEN_AGENTS_BASE-XX#$AGENTS_BASE#" \
    > ./cleanupd
  chmod 750 ./catalogd ./cleanupd ./reviewd
else
  echo ""
  echo " ERROR - setup.sh-Template does not exist."
  echo "         probably you are in the wrong place."
  echo ""
  exit 0
fi

# load the setup and show it
source ./setup.sh
env|grep KRAKEN | sort -u 

# General installation (you have to be in the directory of install script and you have to be root)

TRUNC=`dirname $KRAKEN_AGENTS_BASE`
echo " Making basic directory: $TRUNC"
if ! [ -d "$TRUNC" ]
then
  mkdir -p "$TRUNC"
  chown ${KRAKEN_USER}:${KRAKEN_GROUP} -R $TRUNC
fi

# copy the software
#==================

if [ -d "$KRAKEN_AGENTS_BASE" ]
then
  # make sure to remove completely the previous installed software
  echo " Removing previous installation."
  rm -rf "$KRAKEN_AGENTS_BASE"
fi

echo " Copy agent installation to: $TRUNC"
cp -r ../agents "$TRUNC"
chown ${KRAKEN_USER}:${KRAKEN_GROUP} -R $KRAKEN_AGENTS_BASE

# create log/db structure
#========================

# owner has to be $KRAKEN_USER:$KRAKEN_GROUP, this user runs the process
echo " Make logfile area: $KRAKEN_AGENTS_LOG"
mkdir -p $KRAKEN_AGENTS_LOG
chown ${KRAKEN_USER}:${KRAKEN_GROUP} -R $KRAKEN_AGENTS_LOG

# install and start daemons
#==========================

install reviewd
install catalogd
install cleanupd

# install web pages
#==================

su - ${KRAKEN_USER} -c $KRAKEN_AGENTS_BASE/html/install.sh $KRAKEN_BASE $KRAKEN_AGENTS_BASE

exit 0
