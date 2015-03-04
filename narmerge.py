#
# Merge all nar files in the current directory.
# Separate nar files by SN and SP name and merge its into SNSP.nar
#
# Copyright (c) 2015 Vadim Zaigrin <vadim.zaigrin@emc.com>
#

import os
import re
import random
import shutil

navi = "naviseccli analyzer -archivemerge -data "


def mergelist(pat,list):
    if len(list) > 1:
        tname = "%s_%s.nar" % ( pat, random.randrange(1,10000,1) )
        os.system( navi + list[0] + " " + list[1] + " -out " + tname )
        mergelist(pat,[tname]+list[2:])
        os.remove(tname)
    else:
        mname = "%s.nar" % pat
        shutil.copyfile(list[0],mname)


nars = [ file for file in os.listdir(os.getcwd()) if re.match(".*nar$",file) ]

for snsp in set( [ re.match(r'([A-Z0-9]+_SP[AB]).*',file).group(1) for file in nars ] ):
    mergelist(snsp, [ file for file in nars if re.match(snsp+'.*',file) ] )

