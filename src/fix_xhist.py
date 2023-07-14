#!/usr/bin/env python3
import os, sys, f90nml

RUNID = os.environ['RUNID']
DATAM = os.environ['DATAM']

nml = f90nml.read(sys.argv[1])

# Remove the &NLSTCALL_PP_HIST sections
del nml['nlstcall_pp_hist']

checkpoint_dump_im = nml['nlchistg']['checkpoint_dump_im'][0]
nml['nlchistg']['checkpoint_dump_im'][0] = os.path.join(DATAM, os.path.basename(checkpoint_dump_im))

streqlog = nml['nlcfiles']['streqlog']
nml['nlcfiles']['streqlog'] = os.path.join(DATAM, os.path.basename(streqlog))
# Do we need to pad with blanks?

nml.write(sys.argv[2], force=True)
