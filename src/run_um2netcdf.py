#!/usr/bin/env python3

# Run the netcdf conversion. Assumes monthly files using names set as
# filename_base='$DATAM/${RUNID}a.pa%C'
# Runs in the archive directory

import os, datetime, collections, um2netcdf4, shutil
from pathlib import Path

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
print("REMOVE_FF", os.environ['REMOVE_FF'], REMOVE_FF)
try:
    USE_JOBFS = os.environ['USE_JOBFS'].lower() == 'true'
except KeyError:
    USE_JOBFS = False
if USE_JOBFS:
    PBS_JOBFS = os.environ['PBS_JOBFS']

# This should get the stream names from the model setup, filename_base
prefix = RUNID+'a.p'
# Strip off time zone (if present) and uses the YYYYMMDD part
date = datetime.datetime.strptime(CYLC_TASK_CYCLE_POINT[:8], '%Y%m%d')
nextdate = datetime.datetime.strptime(NEXT_CYCLE[:8], '%Y%m%d')
if not (date!=nextdate and date.day==1 and nextdate.day==1):
    raise Exception("netCDF conversion requires run length to be in months")

for stream in STREAMS:

    print('stream: '+stream)
    if not stream.isalnum():
        # Skip spaces, commas etc
        continue
    # Loop over months
    year = date.year
    month = date.month
    while True:
        tmpdate = datetime.date(year, month, 1)
        monthstr = tmpdate.strftime('%b').lower()
        # Python < 3.8 strftime doesn't zero pad years
        datestr = '%4.4d%s' % (year, monthstr)
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

        # Doesn't seem to be a month iterator in python
        month += 1
        if month == 13:
            month = 1
            year += 1
        if year==nextdate.year and month==nextdate.month:
            break
