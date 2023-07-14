#!/usr/bin/env python3

# Try to diagnose reason for model failure and decide on resubmission
# Cases handled
# 1. Early failure due to an MPI error with model running only a couple of steps
#    Check start and end time in job.status. Could also get step number from job.out
# 2. MOM failure with "Error from ocean_thickness_mod: Free surface penetrating rock! Model unstable."
#    Automatic handling of this with a perturbation shoud depend on how far into the run it got

import os, time, datetime, re, sys

def exists_file(file,retry=5):
    for i in range(retry):
        if os.path.exists(file):
            return True
        else:
            time.sleep(60)
    return False

def get_jobnum(CYLC_SUITE_RUN_DIR, CYLC_TASK_CYCLE_POINT):
    job_file = os.path.join(CYLC_SUITE_RUN_DIR, 'log', 'job', CYLC_TASK_CYCLE_POINT,
                               'coupled', 'NN', 'job')
    re_jobnum = re.compile('export CYLC_TASK_JOB="[\dTZ]*/[a-z]*/([\d]*)')
    for l in open(job_file).readlines():
        if (result := re_jobnum.search(l)):
            return result.group(1)
    raise Exception('Unable to get jobnum')

def check_shortrun(CYLC_SUITE_RUN_DIR, CYLC_TASK_CYCLE_POINT):
    status_file = os.path.join(CYLC_SUITE_RUN_DIR, 'log', 'job', CYLC_TASK_CYCLE_POINT,
                               'coupled', 'NN', 'job.status')
    print(status_file)
    if exists_file(status_file):
        re_init = re.compile('CYLC_JOB_INIT_TIME=([\dT:-]*)')
        re_exit = re.compile('CYLC_JOB_EXIT_TIME=([\dT:-]*)')
        for l in open(status_file).readlines():
            if (result := re_init.search(l)):
                t_init = datetime.datetime.fromisoformat(result.group(1))
            if (result := re_exit.search(l)):
                t_exit = datetime.datetime.fromisoformat(result.group(1))
        if (t_exit - t_init).total_seconds() < 600:
            return True
        else:
            return False
    else:
        raise Exception("No job.status file from coupled task")

CYLC_SUITE_RUN_DIR = os.environ['CYLC_SUITE_RUN_DIR']
CYLC_TASK_CYCLE_POINT = os.environ['CYLC_TASK_CYCLE_POINT']

# This script should only run once to prevent infinite loops.
# Cylc should take care of this, but for an extra check get the TASK_JOB
# number from the model job script
model_task_jobnum = get_jobnum(CYLC_SUITE_RUN_DIR, CYLC_TASK_CYCLE_POINT)
if model_task_jobnum != '01':
    raise Exception(f'Unexpected run with model_task_jobnum={model_task_jobnum}')

if check_shortrun(CYLC_SUITE_RUN_DIR, CYLC_TASK_CYCLE_POINT):
    sys.exit(0)
else:
    raise Exception('Rerunnable early failure not found')
