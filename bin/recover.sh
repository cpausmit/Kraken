#!/bin/bash
usage=" recover.sh  <config> <version> <py> [ <dset>  <fast> ]"
CONF=$1
VERS=$2
PY=$3
DSET=$4
FAST=$5

if [ -z $PY ]
then
    echo " Missing parameters: $usage"
    exit -1
elif [ -z $DSET ]
then
    echo " Making list of datasets to process"
    dsets=`list /cms/store/user/paus/$CONF/$VERS | cut -d / -f 8`
    echo " DATASETS:"
    echo "$dsets"
else
    echo " OK -- recovering: $CONF $VERS $PY *$DSET*"
    dsets=`list /cms/store/user/paus/$CONF/$VERS/*$DSET* | cut -d / -f 8 | sort -u`
    if [ "`echo $dsets | grep "ERROR on remote end: 1"`" != ""  ]
    then
        echo " no matching datasets. EXIT!"
	exit -1
    else
        echo " DATASETS:"
    	echo "$dsets"
    fi
fi

for DSET in $dsets
do
  echo " #=-=-=-=-=-=-=-=-=-= DATASET: $DSET =-=-=-=-=-=-=-=-=-="
  
  # list all physically available files
  echo "list /cms/store/user/paus/$CONF/$VERS/$DSET | grep root | cut -d ' ' -f2 "
  rm -f checkFile-tmp.list
  list /cms/store/user/paus/$CONF/$VERS/$DSET | grep root | cut -d ' ' -f2 > checkFile-tmp.list
  wc -l checkFile-tmp.list
  
  rm    checkFile.list
  touch checkFile.list
  
  for file in `cat checkFile-tmp.list | grep -v ^#`
  do
      id=`echo $file | cut -d '/' -f 9`
      catalog=/home/tier3/cmsprod/catalog/t2mit/$CONF/$VERS/$DSET/Files
      if [ ".`grep $id $catalog 2> /dev/null`" == "." ]
      then
  	echo " $id processing"
  	echo "$file" >> checkFile.list
      fi
  done
  
  # add to the list
  fibsLock.py --config checkFile --cmd="cat /home/tier3/cmsprod/cms/work/fibs/checkFile.list checkFile.list | sort -u > /tmp/new.list; mv /tmp/new.list /home/tier3/cmsprod/cms/work/fibs/checkFile.list" 
  #echo " Sleeping (10sec) to let it process... might not be long enough"
  kickCatalog -q
  #sleep 10
  
  if [ -z $FAST ]
  then
      # new catalog
      generateCatalogs.py $CONF/$VERS $DSET
      
      # remake the web page
      reviewRequests.py --config $CONF --version $VERS --py $PY --pattern $DSET --displayOnly 1
  fi
      
done

if [ -z $FAST ]
then
    synchronizeWeb.py
fi
