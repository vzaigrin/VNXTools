# NarTools
A set of tools for nar files (data files from EMC CLARiiON/VNX) written on Python.

### NarMerge

Merges all nar files in the current directory.
It selects all nar files, separates them by array’s serial number (SN) and storage processor name (SP) and then merges them into files SNSP.nar


### NarExtract

Extracts data from all nar files in the current directory.
It selects all nar files, separates them by array’s serial number (SN) and storage processor name (SP) and then extract data into files SNSP.csv

Both scripts were tested with Python 3, but also should work with Python 2.
