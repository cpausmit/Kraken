#!/bin/bash
usage=" recover.sh  <config> <version> <py> [ <dset> ]"
CONF=$1
VERS=$2
PY=$3
DSET=$4

if [ -z $PY ]
then
  echo " Missing parameters: $usage"
elif [ -z $DSET ]
then
  echo " Making list of datasets to process"
  dsets=`list /cms/store/user/paus/$CONF/$VERS | cut -d / -f 8`
  echo " DATASETS:"
  echo "$dsets"
else
  echo "OK -- recovering: $CONF $VERS $PY $DSET"
  dsets="$DSET"
fi

for DSET in $dsets
do
  echo " #=-=-=-=-=-=-=-=-=-= DATASET: $DSET =-=-=-=-=-=-=-=-=-="
  
  # list all physically available files
  echo "list /cms/store/user/paus/$CONF/$VERS/$DSET | grep root | cut -d ' ' -f2 "
  list /cms/store/user/paus/$CONF/$VERS/$DSET | grep root | cut -d ' ' -f2 > checkFile-tmp.list
  wc -l checkFile-tmp.list
  
  rm    checkFile.list
  touch checkFile.list
  
  for file in `cat checkFile-tmp.list | grep -v ^#`
  do
      id=`echo $file | cut -d '/' -f 9`
      catalog=/home/tier3/cmsprod/catalog/t2mit/$CONF/$VERS/$DSET/Files
      if [ ".`grep $id $catalog`" == "." ]
      then
  	echo " $id processing"
  	echo "$file" >> checkFile.list
      fi
  done
  
  # add to the list
  fibsLock.py --config checkFile --cmd="cat checkFile.list >> /home/tier3/cmsprod/cms/work/fibs/checkFile.list"
  echo " Sleeping (10sec) to let it process... might not be long enough"
  kickCatalog -q
  sleep 10
  
  # new catalog
  generateCatalogs.py $CONF/$VERS $DSET
  
  # remake the web page
  reviewRequests.py --config $CONF --version $VERS --py $PY --pattern $DSET --displayOnly 1

done

synchronizeWeb.py
