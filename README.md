# NarTools
A set of tools for nar files (data files from EMC CLARiiON/VNX) written on Python.

Both scripts call standard naviseccli utility, but prepare data for that call.

### NarMerge

Merges all nar files in the current directory.
It selects all nar files, separates them by array’s serial number (SN) and storage processor name (SP) and then merges them into files SNSP.nar


### NarExtract

Extracts data from all nar files in the current directory.
It selects all nar files, separates them by array’s serial number (SN) and storage processor name (SP) and then extract data into files SNSP.csv
Also it extracts configuration and relations files in XML format.

Both scripts were tested with Python 3, but also should work with Python 2.
