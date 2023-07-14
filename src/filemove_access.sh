#! /bin/bash

set -x

mkdir -p $ARCHIVEDIR/restart/atm
mkdir -p $ARCHIVEDIR/restart/cpl
mkdir -p $ARCHIVEDIR/restart/ice
mkdir -p $ARCHIVEDIR/restart/ocn
mkdir -p $ARCHIVEDIR/history/atm

cd $DATAM

# Move the last restart file to archive. Assuming that UM configuration sets
# dump_filename_base='$DATAM/${RUNID}a.d%z%C'
# so just look for the last file

EXPECTED_NAME=$DATAM/${RUNID}a.da${NEXTDATE}_00
CHECKPOINT_DUMP_IM=$(get_checkpoint_name.py $RUNID.xhist)
if [[ $EXPECTED_NAME != $CHECKPOINT_DUMP_IM ]]; then
    echo "Restart file mismatch" >&2
    echo "Expected name" $EXPECTED_NAME >&2
    echo "Checkpoint name", $CHECKPOINT_DUMP_IM >&2
    exit 1
fi

mv $EXPECTED_NAME ${ARCHIVEDIR}/restart/atm/
if [[ $? != 0 ]]; then
  echo "Error moving atm restart file"
  exit 1
fi
mv ${RUNID}.xhist ${ARCHIVEDIR}/restart/atm/${RUNID}.xhist-${ENDDATE}
if [[ $? != 0 ]]; then
  echo "Error moving atm xhist file"
  exit 1
fi
# These are needed for ozone adjustment so move them now too, even though
# they're strictly not restart files
mv ${RUNID}a.p* $ARCHIVEDIR/history/atm
if [[ $? != 0 ]]; then
  echo "Error moving atm history files"
  exit 1
fi

cd $CPL_RUNDIR

for resfile in ?2?.nc; do
    mv $resfile ${ARCHIVEDIR}/restart/cpl/$resfile-${ENDDATE}
    if [[ $? != 0 ]]; then
      echo "Error moving coupler restart files"
     exit 1
    fi
done

cd $ICE_RUNDIR
mv mice.nc ${ARCHIVEDIR}/restart/ice/mice.nc-${ENDDATE}
if [[ $? != 0 ]]; then
  echo "Error moving mice.nc file"
  exit 1
fi

cd $ICE_RUNDIR/RESTART

# Move the file named in ice.restart_file
mv $(basename $(cat ice.restart_file)) ${ARCHIVEDIR}/restart/ice/
if [[ $? != 0 ]]; then
  echo "Error moving iced files"
  exit 1
fi

mv ice.restart_file ${ARCHIVEDIR}/restart/ice/ice.restart_file-${ENDDATE}
if [[ $? != 0 ]]; then
  echo "Error moving ice.restart file"
  exit 1
fi

cd $OCN_RUNDIR/RESTART
tar -cvf ${ARCHIVEDIR}/restart/ocn/restart-${ENDDATE}.tar *.res*
if [[ $? != 0 ]]; then
  echo "Error in creating ocean restart tar file"
  exit 1
fi
