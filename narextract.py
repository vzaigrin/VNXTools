#
# Extract data from all nar files in the current directory.
# Separate nar files by SN and SP name and output results into file SNSP.csv
#
# Copyright (c) 2015 Vadim Zaigrin <vzaigrin@yandex.ru>
#

import os
import re
import argparse

# Parsing command-line options

parser = argparse.ArgumentParser(description='Extract data from EMC CLARiiON/VNX Nar files')
parser.add_argument('-e','--extend',dest='extend',action='store_true',help='extended mode - extract all information')
parser.add_argument('-o','--object',dest='object', nargs='*',default=[],action='store',help='specifies the objects')
parser.add_argument('-f','--format',dest='format', nargs='*',default=[],action='store',help='specifies performance characteristics')
args = parser.parse_args()

extend = args.extend
object = args.object
format = args.format

nars = [ file for file in os.listdir(os.getcwd()) if re.match(".*nar$",file) ]

for snsp in set( [ re.match(r'([A-Z0-9]+_SP[AB]).*',file).group(1) for file in nars ] ):
    if extend:
        navi = "naviseccli analyzer -messner -archivedump -data "
    else:
        navi = "naviseccli analyzer -archivedump -data "
    navi += ' '.join( [ file for file in nars if re.match(snsp+'.*',file) ] )
    if  len(object) > 0:
        navi += ' -object '
        navi += ' '.join( o for o in object)
    if  len(format) > 0:
        navi += ' -format '
        navi += ' '.join( f for f in format)
    os.system( navi + " -join -overwrite y -out " + snsp + ".csv" )
