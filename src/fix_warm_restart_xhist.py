#!/usr/bin/env python3

# Change xhist file for a warm restart
import os, sys, f90nml

RUNID = os.environ['RUNID']
DATAM = os.environ['DATAM']
ROSE_DATA = os.environ['ROSE_DATA']
WARM_RESTART_DATE = os.environ['WARM_RESTART_DATE']

nml = f90nml.read(sys.argv[1])

# Remove the &NLSTCALL_PP_HIST sections
del nml['nlstcall_pp_hist']

nml['nlchistg']['checkpoint_dump_im'][0] = os.path.join(DATAM, "%sa.da%s_00" % (RUNID, WARM_RESTART_DATE))

nml['nlcfiles']['astart'] = os.path.join(ROSE_DATA, "%s.astart" % RUNID)

nml['nlcfiles']['streqlog'] = os.path.join(DATAM, "%s.stash" % RUNID)

nml.write(sys.argv[2], force=True)
