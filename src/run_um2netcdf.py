#!/usr/bin/env python3

# Run the netcdf conversion. Assumes monthly files using names set as
# filename_base='$DATAM/${RUNID}a.pa%C'
# Runs in the archive directory

import os, datetime, collections, um2netcdf4, shutil, re, f90nml
from pathlib import Path
from dateutil import rrule
from collections.abc import Sequence

CYLC_TASK_CYCLE_POINT = os.environ['CYLC_TASK_CYCLE_POINT']
NEXT_CYCLE = os.environ['NEXT_CYCLE']
RUNID = os.environ['RUNID']
STREAMS = os.environ['NETCDF_STREAMS']
try:
    ARCHIVEDIR = os.environ['ARCHIVEDIR']
    arch = True
except:
    DATAM = os.environ['DATAM']
    arch = False
print("archive (history/atm): ", arch)
REMOVE_FF = os.environ['REMOVE_FF'].lower() == 'true'
print("REMOVE_FF", REMOVE_FF)
try:
    USE_JOBFS = os.environ['USE_JOBFS'].lower() == 'true'
except KeyError:
    USE_JOBFS = False
if USE_JOBFS:
    PBS_JOBFS = os.environ['PBS_JOBFS']

# This should get the stream names from the model setup, filename_base
prefix = RUNID+'a.p'
# Strip off time zone (if present) and uses the YYYYMMDD part
start_date = datetime.datetime.strptime(CYLC_TASK_CYCLE_POINT[:8], '%Y%m%d')
next_date = datetime.datetime.strptime(NEXT_CYCLE[:8], '%Y%m%d')
end_date = next_date - datetime.timedelta(seconds=1)

# Get the reinitialisation unit and frequency from the UM namelist
ATM_RUNDIR=os.environ['ATM_RUNDIR']
nml = f90nml.read(Path(ATM_RUNDIR)/'ATMOSCNTL')
stream_unit = {}
stream_step = {}
# Not a list if there's only a single item
if isinstance(nml['nlstcall_pp'], Sequence):
    iterator = nml['nlstcall_pp']
else:
    iterator = [nml['nlstcall_pp']]
for n in iterator:
    basename = Path(n['filename_base']).name
    # Expected form of the basename
    reg = re.compile(f'{RUNID}a.p([a-z0-9])%C')
    m = reg.match(basename)
    if not m:
        raise Exception("Unexpected string in filename_base in ATMOSCNTL", n['filename_base'])
    stream = m.group(1)
    stream_step[stream] = n['reinit_step']
    if n['reinit_unit']==2:
        stream_unit[stream] = rrule.DAILY
    elif n['reinit_unit']==4:
        stream_unit[stream] = rrule.MONTHLY
    else:
        raise Exception('Stream reinit_unit not supported', n)

# Climate mean has assumed monthly reinit for CM2
mean_basename = ""
try:
    mean_basename = nml['nlstcgen']['mean_1_filename_base']
except KeyError:
    pass
if mean_basename:
    mean_basename = Path(mean_basename).name
    if mean_basename != f'{RUNID}a.p%C':
        raise Exception("Unexpected name for climate mean", mean_basename)
    stream_step['m'] = 1
    stream_unit['m'] = rrule.MONTHLY

for stream in STREAMS:

    if not stream.isalnum():
        # Skip spaces, commas etc
        continue
    # Loop over time
    print(f'stream: {stream}')
    if stream not in stream_unit:
        print(f"Warning: requested stream {stream} not found in model namelist")
        continue
    for date in rrule.rrule(stream_unit[stream], interval=stream_step[stream],
                            dtstart=start_date, until=end_date):

        # Behaviour of the UM %C format
        if stream_unit[stream] == rrule.MONTHLY:
            datestr = date.strftime('%04Y%b').lower()
        else:
            datestr = date.strftime('%04Y%m%d')

        input_file = prefix + stream + datestr
        output_file = input_file + '.nc'
        if arch:
            input_dir = Path(ARCHIVEDIR) / 'history' / 'atm'
        else:
            input_dir = Path(DATAM)
        output_dir = input_dir / 'netCDF'
        output_dir.mkdir(exist_ok = True)
        input = input_dir / input_file
        output = output_dir / output_file
        # Named tuple to hold the argument list
        Args = collections.namedtuple('Args', 'nckind compression simple nomask hcrit verbose include_list exclude_list nohist use64bit')
        args = Args(3, 4, True, False, 0.5, False, None, None, False, False)
        print(input)
        if USE_JOBFS:
            # Copy the files to and from JOBFS
            tmp_input = Path(PBS_JOBFS) / input_file
            tmp_output = Path(PBS_JOBFS) / output_file
            print("jobfs files", tmp_input, tmp_output)
            shutil.copy(input, tmp_input)
            um2netcdf4.process(tmp_input, tmp_output, args)
            tmp_input.unlink()
            shutil.move(tmp_output, output)
        else:
            um2netcdf4.process(input, output, args)
        if REMOVE_FF:
            input.unlink()
