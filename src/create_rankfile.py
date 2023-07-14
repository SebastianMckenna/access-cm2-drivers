#!/usr/bin/env python3
import os
import math

# Get the decomposition from the environment variables defined in suite.rc
um_decomp = {
        'x': int(os.environ['UM_ATM_NPROCX']),
        'y': int(os.environ['UM_ATM_NPROCY']),
        'ios': int(os.environ['FLUME_IOS_NPROC']),
        'omp': int(os.environ['OMP_NUM_THREADS'])}

# mom_decomp = {
#         'x': int(os.environ['OCN_NPROCX']),
#         'y': int(os.environ['OCN_NPROCY'])}

ice_decomp = {
        'n': int(os.environ['ICE_NPROCS'])}

# Total number of MPI ranks for each process
um_nrank = um_decomp['x']*um_decomp['y']+um_decomp['ios']
# mom_nrank = mom_decomp['x']*mom_decomp['y']
mom_nrank = int(os.environ['OCN_NPES'])
cice_nrank = ice_decomp['n']

# Some information about processor layout
slots_per_host = int(os.environ['NSLOTS'])
sockets_per_host = 2
slots_per_socket = slots_per_host / sockets_per_host

share_nodes = os.environ['SHARE_NODES'] == 'true'

# Assume that the number of threads evenly divides a single socket
assert slots_per_socket % um_decomp['omp'] == 0

# Assume each model gets dedicated nodes
assert (math.ceil(um_nrank*um_decomp['omp']/ slots_per_host) +
        math.ceil(mom_nrank / slots_per_host) +
        math.ceil(mom_nrank / slots_per_host)) <= int(os.environ['PBS_NCPUS'])

# Get a list of unique hosts
with open(os.environ['PBS_NODEFILE']) as rankfile:
    pbs_hosts = [x.strip() for x in sorted(set(rankfile.readlines()))]

def write_model_ranks(nranks, start_rank, start_host, omp=1):
    """
    Write out the rankfile for a single model

    Output looks like

        rank 0=+n0 slot=0:0-1

    and defines what host, socket and core each MPI rank is assigned

    See https://www.open-mpi.org/faq/?category=tuning#using-paffinity-v1.3
    """
    for rank in range(nranks):
        host = math.floor(rank * omp / slots_per_host)
        socket = math.floor(rank * omp / slots_per_socket) % sockets_per_host
        core = (rank * omp) % slots_per_socket

        rankfile.write("rank %d=%s slot=%d:%d-%d\n"%(
            rank + start_rank,
            pbs_hosts[int(host + start_host)],
            socket,
            core,
            core+omp-1))

with open(os.path.join(os.environ['CYLC_TASK_WORK_DIR'],'rankfile'),'w') as rankfile:

    # UM processes can get multiple cores, based on OMP_NUM_THREADS
    write_model_ranks(um_nrank, 0, 0, um_decomp['omp'])

    mom_host_start = math.ceil(um_nrank*um_decomp['omp']/ slots_per_host)
    if share_nodes:
        # Start on a clean node but allow MOM and CICE to share node
        write_model_ranks(mom_nrank+cice_nrank, um_nrank, mom_host_start)
    else:
        write_model_ranks(mom_nrank, um_nrank, mom_host_start)
        cice_host_start = mom_host_start + math.ceil(mom_nrank / slots_per_host)
        write_model_ranks(cice_nrank, um_nrank+mom_nrank, cice_host_start)
