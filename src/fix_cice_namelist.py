#!/usr/bin/env python3
import os, sys, f90nml

def reset(namelist, var, value):
    assert namelist[var] == 'set_by_driver'
    namelist[var] = value

# CICE has two namelists
model_basis = [int(i) for i in os.environ['MODELBASIS'].split(',')]
byear, bmon, bday = model_basis[:3]
runlen_sec = 86400*int(os.environ['RUN_DAYS'])
dt_ice = int(os.environ['DT_ICE'])
cice_steps = runlen_sec // dt_ice

nml = f90nml.read(sys.argv[1])

reset(nml['setup_nml'], 'days_per_year', int(os.environ['DAYS_THIS_YEAR']))
reset(nml['setup_nml'], 'year_init', byear)
reset(nml['setup_nml'], 'npt', cice_steps)
reset(nml['setup_nml'], 'dt', dt_ice)
reset(nml['setup_nml'], 'runtype', os.environ['ICE_RUNTYPE'])
# Set restart to be consistent with runtype
reset(nml['setup_nml'], 'restart', os.environ['ICE_RUNTYPE']=='continue')
reset(nml['domain_nml'], 'nprocs', int(os.environ['ICE_NPROCS']))

nml.write(sys.argv[1], force=True)

nml = f90nml.read(sys.argv[2])

# jobnum = 1 for an initial run, 2 for continue
if os.environ['ICE_RUNTYPE']=='continue':
    jobnum = 2
else:
    jobnum = 1
reset(nml['coupling'], 'jobnum', jobnum)
reset(nml['coupling'], 'inidate', int(os.environ['INITDATE']))
reset(nml['coupling'], 'runtime', runlen_sec)
reset(nml['coupling'], 'runtime0', 86400*int(os.environ['START_DAYS']))
reset(nml['coupling'], 'init_date', byear*10000 + bmon*100 + bday)
reset(nml['coupling'], 'dt_cpl_ai', int(os.environ['DT_CPL_AI']))
reset(nml['coupling'], 'dt_cpl_io', int(os.environ['DT_CPL_IO']))
reset(nml['coupling'], 'dt_cice', dt_ice)

nml.write(sys.argv[2], force=True)
