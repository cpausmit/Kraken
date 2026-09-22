#!/bin/bash
#---------------------------------------------------------------------------------------------------
# Install the (all-Python, static-output) dashboard web environment. Should be done once at
# installation phase only -- the daemon (dashboardd) regenerates status.json on its own cycle,
# this script just seeds the static assets (HTML/CSS/JS/images) and does the initial rsync.
#
# Author: C.Paus                                                                     (Sep 01, 2026)
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
echo " $0 -> installing the dashboard"
echo " "

# images
echo " Copy images from $KRAKEN_BASE"
cp $KRAKEN_BASE/agents/dashboard/images/{Kraken,agent}*jpg \
   $KRAKEN_BASE/agents/dashboard/images/kraken.png \
   $KRAKEN_AGENTS_LOG

# static dashboard assets (HTML/CSS/JS) -- these are never regenerated per-cycle, only status.json is
echo " Copy dashboard assets"
cp $KRAKEN_BASE/agents/dashboard/style.css \
   $KRAKEN_BASE/agents/dashboard/index.html \
   $KRAKEN_BASE/agents/dashboard/detail.html \
   $KRAKEN_BASE/agents/dashboard/dashboard.js \
   $KRAKEN_AGENTS_LOG

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
