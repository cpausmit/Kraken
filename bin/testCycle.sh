#!/bin/bash

# load updated config
source $KRAKEN_BASE/agents/cycle.cfg
env |grep KRAKEN

# loop over all requested configurations
for reqset in $KRAKEN_REVIEW_CYCLE
do

  echo " ReqSet: $reqset"

  cfg=`echo $reqset | cut -d: -f1`
  vrs=`echo $reqset | cut -d: -f2`
  pys=`echo $reqset | cut -d: -f3`

  for py in `echo $pys | tr ',' ' '`
  do

    echo " cfg: $cfg, vrs: $vrs, py: $py"

  done

done      
