#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Install the web environment (should be done once at installation phase only). Make sure the
# environment is setup correctly
# 
#
# Author: C.Paus                                                                     (May 14, 2015)
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
echo " Using Kraken base:  $BASE"
echo " Kraken agents base: $AGENTS_BASE"
echo ""

source $AGENTS_BASE/setup.sh

# Message at the begining
echo " "
echo " $0 -> installing the web pages"
echo " "

# images
echo " Copy images from $KRAKEN_BASE"
cp $KRAKEN_BASE/agents/html/images/{Kraken,agent}*jpg \
   $KRAKEN_AGENTS_LOG

# global index files to log area
echo " Generate index files"
cat $KRAKEN_BASE/agents/html/index.php \
   | sed "s@XX-KRAKEN_BASE-XX@$KRAKEN_BASE@" \
   > $KRAKEN_AGENTS_LOG/index.php

# agent specific index files
cat $KRAKEN_BASE/agents/html/index.php-Template \
   | sed 's/XX-NAME-XX/reviewd/g' | sed 's/XX-AKA-XX/Smith/' \
   | sed "s@XX-KRAKEN_BASE-XX@$KRAKEN_BASE@" \
   > $KRAKEN_AGENTS_LOG/reviewd/index.php
cat $KRAKEN_BASE/agents/html/index.php-Template \
   | sed 's/XX-NAME-XX/catalogd/g' | sed 's/XX-AKA-XX/Johnson/' \
   > $KRAKEN_AGENTS_LOG/catalogd/index.php
cat $KRAKEN_BASE/agents/html/index.php-Template \
   | sed 's/XX-NAME-XX/monitord/g' | sed 's/XX-AKA-XX/Brown/' \
   > $KRAKEN_AGENTS_LOG/monitord/index.php
cat $KRAKEN_BASE/agents/html/index.php-Template \
   | sed 's/XX-NAME-XX/cleanupd/g' | sed 's/XX-AKA-XX/Williams/' \
   > $KRAKEN_AGENTS_LOG/cleanupd/index.php

# update web pages from log area
echo " Sync files to the web area - no deletions"
echo " - $KRAKEN_AGENTS_LOG --> $KRAKEN_AGENTS_WWW/../"
mkdir -p    $KRAKEN_AGENTS_WWW 
rsync -Cavz $KRAKEN_AGENTS_LOG $KRAKEN_AGENTS_WWW/../

if [ "`whoami`" != "${KRAKEN_USER}" ]
then
  whoami
  echo " chown ${KRAKEN_USER}:${KRAKEN_GROUP} -R $KRAKEN_AGENTS_LOG $KRAKEN_AGENTS_WWW"
  echo " --- wait this might take a while"
  chown ${KRAKEN_USER}:${KRAKEN_GROUP} -R $KRAKEN_AGENTS_LOG $KRAKEN_AGENTS_WWW
fi
exit 0
