#!/usr/bin/python

#
# Extract SP_arrayconfig.xml file from all SPCollect files in the current directory.
# Separate SPCollect files by SN and SP name and output results into file SN_SP_arrayconfig.xml
#
# Copyright (c) 2017 Vadim Zaigrin <vzaigrin@yandex.ru>
#

import os
import re
import zipfile

zips = [file for file in os.listdir(os.getcwd()) if re.match(".*_data.zip$", file)]

for file in zips:
    sn = re.match(r'([A-Z0-9]+)_SP[AB].*',file).group(1)
    datazip = zipfile.ZipFile(file)
    susname = [file for file in datazip.namelist() if re.match(".*_sus.zip$", file)][0]
    datazip.extract(susname)
    suszip = zipfile.ZipFile(susname)
    acname = [file for file in suszip.namelist() if re.match("SP[AB]_arrayconfig.xml$", file)][0]
    suszip.extract(acname)
    os.remove(susname)
    os.rename(acname, sn + "_" + acname)

