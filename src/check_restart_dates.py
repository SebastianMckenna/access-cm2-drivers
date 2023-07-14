#!/usr/bin/env python3
import os, re, sys, f90nml

RUNID = os.environ['RUNID']
DATAM = os.environ['DATAM']
CYLC_TASK_CYCLE_POINT = os.environ['CYLC_TASK_CYCLE_POINT']

# Get date from cycle point
cycle_date = CYLC_TASK_CYCLE_POINT.split('T')[0]

# Date from xhist file
xhistfile = os.path.join(DATAM,'%s.xhist'%RUNID)

xhist_date = ''
nml = f90nml.read(xhistfile)
checkpoint_dump_im = os.path.basename(nml['nlchistg']['checkpoint_dump_im'][0])
match = re.search(r"\S*da(\d{8})", checkpoint_dump_im)
if match:
    xhist_date = match.group(1)

if not xhist_date:
    sys.exit('Failed to get date from xhist file')

if cycle_date == xhist_date:
    print('UM restart date matches cycle date')
else:
    sys.exit('ERROR - Date mismatch: cycle date %s, UM restart date %s' % (cycle_date, xhist_date))
