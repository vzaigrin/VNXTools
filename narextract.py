#
# Extract data from all nar files in the current directory.
# Separate nar files by SN and SP name and output results into file SNSP.nar
#
# Copyright (c) 2015 Vadim Zaigrin <vadim.zaigrin@emc.com>
#

import os
import re

nars = [ file for file in os.listdir('.') if re.match(".*nar$",file) ]

for snsp in set( [ re.match(r'([A-Z0-9]+_SP[AB]).*',file).group(1) for file in nars ] ):
    navi = "naviseccli analyzer -archivedump -data "
    for file in [ file for file in nars if re.match(snsp+'.*',file) ]: navi += file + " "
    os.system( navi + " -join -overwrite y -out " + snsp + ".csv" )

