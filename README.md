# VNXTools
A set of tools for EMC CLARiiON/VNX.

Some tools work with NAR files - performance data files - and call standard naviseccli utility.


### NarMerge

Merges all NAR files in the current directory.
It selects all NAR files, separates them by array’s serial number (SN) and storage processor name (SP) and then merges them into files SNSP.nar

### NarExtract

Extracts data from all NAR files in the current directory.
It selects all NAR files, separates them by array’s serial number (SN) and storage processor name (SP) and then extract data into files SNSP.csv
Also it extracts configuration and relations files in XML format.

### NarConfiguration

Generates configuration visualization diagram in the GraphViz format by the relations information extracted from the NAR file.

### VNXConfigDiagram

Generates configuration visualization diagram in the GraphViz format by the array configuration information extracted from the 'live' array.

All scripts were tested with Python 3, but also should work with Python 2.
