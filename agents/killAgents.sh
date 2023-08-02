#!/bin/bash
# --------------------------------------------------------------------------------------------------
# Killing all active agents to start clean.
#
#                                                                Ch.Paus: Version 0.0 (Apr 27, 2015)
# --------------------------------------------------------------------------------------------------

function killAgent {
  # function that will install the daemon named as the given first parameter
  #   example: install reviewd

  # command line parameter
  daemon="$1" 
  process="$2"

  # stop potentially existing server process
  if [ -e "/etc/init.d/${daemon}" ]
  then
    /etc/init.d/${daemon} status
    /etc/init.d/${daemon} stop
  fi

  killall $daemon
  if ! [ -z "$process" ]
  then
    killall $process
  fi
  list=`ps auxw |grep $KRAKEN_USER|grep -v grep|grep jobSitter|tr -s ' '|cut -d ' ' -f2`
  if [ "$list" != "" ]
  then
    kill $list
  fi

  ps auxw |grep $KRAKEN_USER | grep -v grep | grep $daemon  
  if ! [ -z "$process" ]
  then
    ps auxw |grep $KRAKEN_USER | grep -v grep | grep $process
  fi

}
#---------------------------------------------------------------------------------------------------
#                                               M A I N
#---------------------------------------------------------------------------------------------------
# Setup the environment
source ../setup.sh
source ./setup.sh

# kill all daemons and main processes inside
#===========================================

killAgent reviewd reviewRequests.py
killAgent catalogd
killAgent monitord
killAgent cleanupd reviewRequests.py

exit 0
