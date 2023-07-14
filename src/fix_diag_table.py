#!/usr/bin/env python3

# diag_table file is not a namelist so use string search and replace

import os, sys

diag_table = open(sys.argv[1]).read()

# Check text to be replaced is present
tmp = diag_table.index('#SYEAR #SMON #SDAY')

model_basis = [int(i) for i in os.environ['MODELBASIS'].split(',')]
byear, bmon, bday = model_basis[:3]
newstring = '%d %d %d' % (byear, bmon, bday)

diag_table = diag_table.replace('#SYEAR #SMON #SDAY', newstring)

open(sys.argv[1], 'w').write(diag_table)
