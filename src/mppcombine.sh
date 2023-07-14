#!/bin/bash

ulimit -s unlimited

cd $OCN_RUNDIR/HISTORY
for histfile in *.nc.0000; do
   basefile=${histfile%.*}              #drop the suffix '.0000'!
   output=$ARCHIVEDIR/history/ocn/$basefile-${ENDDATE}
  #remove existing output from previous run
  if [[ -f $output ]]; then
    echo "Output file $output exists, removing"
    rm $output
  fi  
  ~access/access-cm2/utils/mppnccombine_nc4 -n4 -z -v -r $output ${basefile}.????
done

