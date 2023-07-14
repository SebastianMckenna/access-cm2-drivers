#!/usr/bin/env bash

set -xeu

echo "ACCESS COUPLED MODEL WARM RESTART SETUP"

mkdir -p $OCN_RUNDIR/INPUT
mkdir -p $ICE_RUNDIR/RESTART
mkdir -p $CPL_RUNDIR

# This is a continuation run so copy the restart files
# ENDDATE from the previous run
PREVDATE=$(cylc cyclepoint --offset=-P1D --template=CCYYMMDD ${WARM_RESTART_DATE})
cp ${WARM_RESTART_DIR}/restart/cpl/a2i.nc-${PREVDATE} $CPL_RUNDIR/a2i.nc
cp ${WARM_RESTART_DIR}/restart/cpl/o2i.nc-${PREVDATE} $CPL_RUNDIR/o2i.nc
cp ${WARM_RESTART_DIR}/restart/cpl/i2a.nc-${PREVDATE} $CPL_RUNDIR/i2a.nc

mkdir -p ${DATAM}

# Force variable to lower case for case insensitive comparison
if [ ${WARM_RESTART_NRUN,,} = "true" ]; then
    # Expect that only the perturbed ensemble uses this
    TARGET=${ASTART:-$ROSE_DATA/$RUNID.astart}
    cp ${WARM_RESTART_DIR}/restart/atm/${WARM_RESTART_RUNID}a.da${WARM_RESTART_DATE}_00   $TARGET
     # If necessary change the date of the restart file
     if [[ $CYLC_SUITE_INITIAL_CYCLE_POINT != $WARM_RESTART_DATE ]]; then
	 rose date --print-format="%Y %m %d" ${CYLC_SUITE_INITIAL_CYCLE_POINT} |  python3 ~access/apps/pythonlib/umfile_utils/access_cm2/change_dump_date.py  $TARGET
    fi
else  # Regular warm start
    if [ ${RECON,,} != "true" ]; then
	cp ${WARM_RESTART_DIR}/restart/atm/${WARM_RESTART_RUNID}a.da${WARM_RESTART_DATE}_00 ${DATAM}/${RUNID}a.da${WARM_RESTART_DATE}_00
	# Change name of checkpoint dump in xhist file to new version
	fix_warm_restart_xhist.py ${WARM_RESTART_DIR}/restart/atm/${WARM_RESTART_RUNID}.xhist-${PREVDATE} ${DATAM}/${RUNID}.xhist
    fi
fi

cd $OCN_RUNDIR/INPUT

if [ -f ${WARM_RESTART_DIR}/restart/ocn/restart-${PREVDATE}.tar ]; then
# New style tar file
  tar -xf ${WARM_RESTART_DIR}/restart/ocn/restart-${PREVDATE}.tar
else
# Old single files
    for restfile in ${WARM_RESTART_DIR}/restart/ocn/*-${PREVDATE}; do
	newfile=${restfile##*/}
	cp ${restfile} ${newfile%-*}
    done
fi

# Fix date in ocean_solo.res
echo 3 >ocean_solo.res
rose date --print-format='%Y %m %d %H %M %S' ${BASIS} >> ocean_solo.res
rose date --print-format='%Y %m %d %H %M %S' ${INITDATE} >> ocean_solo.res

cd $ICE_RUNDIR/RESTART

cp ${WARM_RESTART_DIR}/restart/ice/ice.restart_file-${PREVDATE} 	ice.restart_file
# Get the file named in ice.restart_file
cp ${WARM_RESTART_DIR}/restart/ice/$(basename $(cat ice.restart_file)) .
cp ${WARM_RESTART_DIR}/restart/ice/mice.nc-${PREVDATE} 	  	mice.nc
