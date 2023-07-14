#!/usr/bin/env python3


from __future__ import division, print_function
import os, sys, f90nml

def replace_string(namcouple, target, value):
    # Check that the target string is present at least once
    tmp = namcouple.index(target)
    return  namcouple.replace(target, value)

runlen_sec = 86400*int(os.environ['RUN_DAYS'])

nml = f90nml.read(os.path.join(os.environ['ATM_RUNDIR'], 'ATMOSCNTL'))
dt_atm = nml['nlstcgen']['secs_per_periodim'] // nml['nlstcgen']['steps_per_periodim']

namcouple = open(sys.argv[1]).read()

# Model names are set in source code
namcouple = replace_string(namcouple, '#Mod1_name', 'toyatm')
namcouple = replace_string(namcouple, '#Mod2_name', 'mom5xx')
namcouple = replace_string(namcouple, '#Mod3_name', 'cicexx')
namcouple = replace_string(namcouple, '#Runtime_sec', '%d' % runlen_sec)
namcouple = replace_string(namcouple, '#NLOGPRT', os.environ['NLOGPRT'])
namcouple = replace_string(namcouple, '#CPL_intv_ai', os.environ['DT_CPL_AI'])
namcouple = replace_string(namcouple, '#CPL_intv_io', os.environ['DT_CPL_IO'])
namcouple = replace_string(namcouple, '#DT_ATM', '%d' % dt_atm)
namcouple = replace_string(namcouple, '#DT_ICE', os.environ['DT_ICE'])
# These are not used in the template file
# namcouple = replace_string(namcouple, '#DT_OCN', os.environ['DT_OCN'])
# namcouple = replace_string(namcouple, '#UM_grid', os.environ['um_grid'])

open(sys.argv[1], 'w').write(namcouple)
