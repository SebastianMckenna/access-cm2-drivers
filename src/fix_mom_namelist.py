#!/usr/bin/env python3
import os, sys, f90nml

def reset(namelist, var, value):
    assert namelist[var] == 'set_by_driver'
    namelist[var] = value

nml = f90nml.read(sys.argv[1])

reset(nml['auscom_ice_nml'],'dt_cpl', int(os.environ['DT_CPL_IO']))

model_basis = [int(i) for i in os.environ['MODELBASIS'].split(',')]
reset(nml['ocean_solo_nml'], 'date_init', model_basis)

reset(nml['ocean_solo_nml'], 'days', int(os.environ['RUN_DAYS']))
reset(nml['ocean_solo_nml'], 'dt_cpld', int(os.environ['DT_CPL_IO']))

reset(nml['ocean_model_nml'], 'dt_ocean',  int(os.environ['DT_OCN']))
reset(nml['ocean_model_nml'], 'layout',
      [int(os.environ['OCN_NPROCX']),int(os.environ['OCN_NPROCY'])])

reset(nml['ocean_velocity_nml'], 'truncate_velocity', os.environ['TRUNCATE']=='.true.')
reset(nml['ocean_velocity_nml'], 'truncate_verbose', os.environ['TRUNCATE']=='.true.')

nml.write(sys.argv[1], force=True)
