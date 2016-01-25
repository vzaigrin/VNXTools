#
# Extract data from all nar files in the current directory.
# Separate nar files by SN and SP name and output results into file SNSP.csv
# Also extract configuration and relation information from last nar file for every SN and SP.
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
        navi = "naviseccli analyzer -messner -archivedump"
    else:
        navi = "naviseccli analyzer -archivedump"
    files = [ file for file in nars if re.match(snsp+'.*',file) and os.stat(file).st_size > 0 ]
    os.system( navi + " -config " + files[-1] + " -xml -overwrite y -out " + snsp + "_config.xml" )
    os.system( navi + " -rel " + files[-1] + " -xml -overwrite y -out " + snsp + "_rel.xml" )
    navi += " -data " + ' '.join(files)
    if  len(object) > 0:
        navi += " -object " + ' '.join( o for o in object)
    if  len(format) > 0:
        navi += " -format " + ' '.join( f for f in format)
    os.system( navi + " -join -overwrite y -out " + snsp + ".csv" )