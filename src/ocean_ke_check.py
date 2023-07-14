#!/usr/bin/env python3

# Call with ocean_scalar.nc as argument

import sys, netCDF4, argparse

parser = argparse.ArgumentParser(description="Check ocean KE")
parser.add_argument('--kmax', dest='kmax', type=float,
                    default=1500, help="KE limit")

parser.add_argument('input', help='Input ocean scalar file')
args = parser.parse_args()

d = netCDF4.Dataset(args.input)

ke = d.variables['ke_tot'][:]
kmax = ke.max()
print('Max ocean KE %.0f' % kmax)

if kmax > args.kmax:
    print("Stopping run because ocean KE %.0f exceeds limit" % kmax, file=sys.stderr)
    sys.exit(1)
