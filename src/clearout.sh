#!/usr/bin/env bash

# Clearout any old data left over from a previous run.

set -u

rm $DATAM/${RUNID}a*
rm $DATAM/${RUNID}.apstmp1
rm $DATAM/${RUNID}.apsum1
rm $DATAM/${RUNID}.xhist
# rm $NEMO_DATA/${RUNID}o*
# rm $NEMO_DATA/namelist
# rm $CICE_DATA/${RUNID}i*
# rm $CICE_DATA/ice.restart_file

# If anything fails then that is still OK so therefore exit with code zero
exit 0
