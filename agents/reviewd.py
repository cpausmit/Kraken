#!/usr/bin/python
# --------------------------------------------------------------------------------------------------
# Process to keep request review alive and well.
#
# v1.0                                                                         C.Paus (Apr 27, 2015)
# --------------------------------------------------------------------------------------------------
# initialize environment variables

source $KRAKEN_AGENTS_BASE/setupAgents.sh

# daemon
daemon=`basename $0`

# go to work area
cd $KRAKEN_AGENTS_WORK
echo ""
echo " Work area: "`pwd`
echo ""

# infinite loop
while [ 1 ]
do

  # make sure the log/web directories exists
  mkdir -p $KRAKEN_AGENTS_LOG/${daemon}
  mkdir -p $KRAKEN_AGENTS_WWW 

  if [ -e "$KRAKEN_AGENTS_LOG/${daemon}" ] && [ -e "$KRAKEN_AGENTS_WWW" ]
  then
    #echo " Request review log/web areas exists. Let's start!"
    sleep 1
  else
    echo ""
    echo " reviewd: Log/web area not found ($KRAKEN_AGENTS_LOG/${daemon},$KRAKEN_AGENTS_WWW)."
    echo " EXIT!"
    echo ""
    exit 1
  fi

  # generate specific log file (to be used once logfile detaches)
  tag=`date "+%s"`
  logFile=$KRAKEN_AGENTS_LOG/${daemon}/${daemon}.log
  rm -r $logFile
  touch $logFile
  echo ""                                                                          >> $logFile
  echo " = = = =  I N I T I A L  M I T _ P R O D   E N V I R O N M E N T  = = = =" >> $logFile
  echo ""                                                                          >> $logFile
  env  | grep ^KRAKEN                                                              >> $logFile
  echo ""                                                                          >> $logFile
  echo " = = = =  I N I T I A L  R E V I E W   E N V I R O N M E N T  = = = ="     >> $logFile
  echo ""                                                                          >> $logFile
  env  | grep ^KRAKEN_REVIEW                                                       >> $logFile
  echo ""                                                                          >> $logFile
  echo "[ PYTHON PATH: $PYTHONPATH ]"                                              >> $logFile
  echo ""                                                                          >> $logFile

  # ten loops over the process with one logfile (keep it small)
  for index in `echo 0 1 2 3 4 5 6 7 8 9`
  do
    # period 3600 * nHours
    let wait=3600*$KRAKEN_REVIEW_CYCLE_HOURS
    echo " "                                                                      >> $logFile
    echo " request review loop $index started -- $tag (cycle wait $wait sec)"     >> $logFile
    echo " "                                                                      >> $logFile
    echo "   --> "`date`                                                          >> $logFile
    echo " "                                                                      >> $logFile


    # load updated config
    source $KRAKEN_BASE/agents/cycle.cfg
    env |grep KRAKEN_REVIEW_CYCLE                                                 >> $logFile
    
    # loop over all requested configurations
    for reqset in $KRAKEN_REVIEW_CYCLE
    do
    
      echo " ==== Request Set: $reqset"                                           >> $logFile
    
      cfg=`echo $reqset | cut -d: -f1`
      vrs=`echo $reqset | cut -d: -f2`
      pys=`echo $reqset | cut -d: -f3`
    
      for py in `echo $pys | tr ',' ' '`
      do
    
        echo " ====-- cfg: $cfg, vrs: $vrs, py: $py"                              >> $logFile
        echo " "                                                                  >> $logFile

          # Display only stuff
          #===================
    
          stdbuf -o0 -e0 \
          $KRAKEN_BASE/bin/reviewRequests.py --config=$cfg --version=$vrs --py=$py \
                 --displayOnly=1 >  $KRAKEN_AGENTS_LOG/${daemon}/status-$py
    
          # make sure ascii files get 'dressing'
          $KRAKEN_BASE/bin/htmlDressing.py --input=$KRAKEN_AGENTS_LOG/${daemon}/status-$py \
                                          --version=$vrs

          # keep log files up to speed
          rsync -Cavz $KRAKEN_AGENTS_LOG/${daemon} $KRAKEN_AGENTS_WWW >& /dev/null
    
          # Full submit cycle
          #==================
          # NOTE --exe is not a valid reviewRequests.py option either, so this call still
          # dies on getopt and submits nothing.  The likely intent is --submit (which
          # defaults to False), but turning job submission back on is an operational
          # decision, so it is left as-is rather than changed silently.

          stdbuf -o0 -e0 \
          $KRAKEN_BASE/bin/reviewRequests.py --config=$cfg --version=$vrs --py=$py --exe \
                                            $KRAKEN_REVIEW_OPTIONS                >> $logFile 2>&1
          echo " "                                                                >> $logFile
    
          # keep log file up to speed
          rsync -Cavz $KRAKEN_AGENTS_LOG/${daemon} $KRAKEN_AGENTS_WWW >& /dev/null
        
      done
    
    done      

    echo " completed review cycle."                                               >> $logFile
    echo " FINISH by updating log files on web."                                  >> $logFile

    rsync -Cavz --delete $KRAKEN_AGENTS_LOG/${daemon} $KRAKEN_AGENTS_WWW          >> $logFile 2>&1
    sleep $wait
  done

  # move completed log file to a dated version before starting over
  mv $logFile $KRAKEN_AGENTS_LOG/${daemon}/${daemon}-${tag}.log

done

exit 0;
