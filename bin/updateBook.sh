#!/bin/bash

mydaemon=reviewd
if [ -z "$1" ]
then
    echo "usage: updateBook.sh <book> [ <py> = nano] (ex. nanoao/533)"
    exit -1
fi
book=$1
cfg=`echo $book | cut -d/ -f1`
vrs=`echo $book | cut -d/ -f2`

if [ -z "$2" ]
then
    py="nano"
else
    py="$2"
fi

echo " making status files"

stdbuf -o0 -e0 \
  $KRAKEN_BASE/bin/reviewRequests.py --config=$cfg --version=$vrs --py=$py \
       --displayOnly=1 >>  $KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/status-$py

# make sure ascii files get 'dressing'
echo " beautify status files"
$KRAKEN_BASE/bin/htmlDressing.py --version=$vrs \
                 --input=$KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/status-$py


rm -f $KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/incomplete-$py
touch $KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/incomplete-$py

echo "#"        >> $KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/incomplete-$py
echo "# "`date` >> $KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/incomplete-$py
echo "#"        >> $KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/incomplete-$py

echo " making incomplete status files"
stdbuf -o0 -e0 \
  $KRAKEN_BASE/bin/reviewRequests.py --config=$cfg --version=$vrs --py=$py \
       --displayOnly=2 >>  $KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/incomplete-$py

# make sure ascii files get 'dressing'
echo " beautify incomplete status files"
$KRAKEN_BASE/bin/htmlDressing.py --version=$vrs \
                 --input=$KRAKEN_AGENTS_LOG/${mydaemon}/${cfg}/${vrs}/incomplete-$py

# keep log files up to speed
synchronizeWeb.py

exit 0
