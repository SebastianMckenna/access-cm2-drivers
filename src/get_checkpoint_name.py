#!/usr/bin/env python3
import sys, f90nml

nml = f90nml.read(sys.argv[1])
checkpoint_dump_im = nml['nlchistg']['checkpoint_dump_im'][0]
print(checkpoint_dump_im.strip())
