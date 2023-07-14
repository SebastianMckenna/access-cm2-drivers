#!/usr/bin/env python3

# Convert CICE history to netCDF4 and combine separate daily files
# into a single monthly file.

# Note that adding shuffle actually increases the size of the
# monthly files.

# Should be run in the CICE history output directory

import os, glob, re, subprocess, calendar

# Expect that all files have prefix iceh

# Check for end of string so as not to match nc4 files etc.
# Rename to iceh_m and iceh_d so that they don't match.

verbose = True
re_monthly = re.compile("iceh.\d\d\d\d-\d\d.nc")
re_daily = re.compile("iceh.\d\d\d\d-\d\d-\d\d.nc")
monthly = []
for f in glob.glob('iceh.*.nc'):
    m = re_monthly.match(f)
    if m:
        monthly.append(f)
        continue
    m = re_daily.match(f)
    if m:
        continue
    raise Exception("Unexpected file %s" % f)

if not monthly:
    print("No files to process")

monthly.sort()

cal = calendar.Calendar()
for f in monthly:
    # Note that spaces are not allowed in subprocess arguments
    cmd = ["nccopy", "-k3", "-d4", f, "iceh_m%s" % f[4:]]
    if verbose:
        print(cmd)
    subprocess.check_call(cmd, stderr=subprocess.STDOUT)

    year = int(f[5:9])
    month = int(f[10:12])

    cmd = ["ncrcat", "-4", "--deflate", "4"]
    for date in cal.itermonthdates(year,month):
        # Days of this month (assuming proleptic Gregorian)
        # This returns days of preceding and following months
        # to give complete weeks, so need to check actual month.
        if date.month == month:
            # strftime doesn't format years before 1000 properly
            cmd.append("iceh.%4.4d-%2.2d-%2.2d.nc" %
                       (date.year, date.month, date.day))
    cmd.append("iceh_d%s" % f[4:])
    if verbose:
        print(cmd)
    subprocess.check_call(cmd, stderr=subprocess.STDOUT)
