#!/bin/bash

mkdir -p $ARCHIVEDIR/history/atm
mkdir -p $ARCHIVEDIR/history/cpl
mkdir -p $ARCHIVEDIR/history/ice
mkdir -p $ARCHIVEDIR/history/ocn

ulimit -s unlimited

# Diagnostic coupling fields output (if any), e.g., fields_i2o_in_ice.nc etc.
for subrundir in $ATM_RUNDIR $ICE_RUNDIR $OCN_RUNDIR; do
  cd $subrundir
  if [[ $(ls fields*.nc | wc -w) -gt 0 ]]; then
    for tmpfile in fields*.nc; do
      mv -f ${tmpfile} ${ARCHIVEDIR}/restart/cpl/${tmpfile}_${ENDDATE}
    done
  fi
done

cd $ICE_RUNDIR/HISTORY
module load netcdf nco
ice_nc4.py
if [ "$?" != "0" ]; then
    echo "Error in ice_nc4.py"
    exit 1
fi
for histfile in iceh_[dm]*; do
  # Fix the calendar
  ncatted -a calendar,time,m,c,proleptic_gregorian ${histfile}
  mv -f ${histfile} ${ARCHIVEDIR}/history/ice
done

cd $OCN_RUNDIR/HISTORY

# COSIMA style diagnostics already have the year and month in the filename
# Original CM2 style do not
if compgen -G "*${THISYEAR}*.0000" > /dev/null; then
  COSIMA_STYLE=true
  SUFFIX=""
else
  COSIMA_STYLE=false
  SUFFIX="-${ENDDATE}"
fi

if [ -e ocean_scalar*.nc ]; then
  for file in ocean-scalar*.nc; do
    ncatted -a calendar,time,m,c,proleptic_gregorian -a calendar_type,time,d,, $file
    mv $file $ARCHIVEDIR/history/ocn/${file}${SUFFIX}
  done
fi
for histfile in *.nc.0000; do
  basefile=${histfile%.*}              #drop the suffix '.0000'!
  output=$ARCHIVEDIR/history/ocn/${basefile}${SUFFIX}
  #remove existing output from previous run
  if [[ -f $output ]]; then
    echo "Output file $output exists, removing"
    rm $output
  fi
  ~access/access-cm2/utils/mppnccombine_nc4 -n4 -z -v -r $output ${basefile}.????
  # Fix the calendar
  ncatted -a calendar,time,m,c,proleptic_gregorian -a calendar_type,time,d,, $output
done
