#
# Generate a description of configuration of EMC CLARiiON/VNX storage aray.
#
# It takes a relation information extracted from a NAR file and generate a configuration diagram in a Graphviz format.
#
# Copyright (c) 2016 Vadim Zaigrin <vzaigrin@yandex.ru>
#

import argparse
import sys
import re
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description='Generate a configuration description by relation information extracted from EMC CLARiiON/VNX Nar file.')
parser.add_argument('-i','--input',dest='input',action='store',nargs=1,help='name of input file')
parser.add_argument('-c','--compact',dest='compact',action='store_true',help='compact form of a diagram')
parser.add_argument('-f','--file',dest='file',nargs=1,default=[],action='store',help='name of the output file')
args = parser.parse_args()

inputfile = args.input[0]
compact = args.compact
tofile= False
if len(args.file) > 0:
    tofile = True
    outputfile = args.file[0]

lunr = re.compile( "([-A-Za-z0-9_ ]+) \[([0-9]+)([-A-Za-z0-9_; ]+)\]" )

tree = ET.parse(inputfile)
root = tree.getroot()

arrayname = root.findall(".//object[@type='Subsystem']")[0].get('name')

hosts = set()
lunhosts = []
for lun in root.findall(".//object[@type='SP']//object[@type='Public RaidGroup LUN']") + \
           root.findall(".//object[@type='SP']//object[@type='Pool Public LUN']"):
    if len(lun.getchildren()) > 0:
        for child in lun.getchildren():
            host = child.get('name')
            hosts.add(host)
            lunhosts += [ ( lunr.match(lun.get('name')).group(2), host ) ]

hosts = list(hosts)

luns = {}
pools = []
lunpools = []
disks = []
diskpools = []
for pool in root.findall(".//object[@type='RAID Group']") + root.findall(".//object[@type='Pool']"):
    pname = re.sub( 'Raid Group', 'RG', pool.get('name') )
    pools += [ pname ]
    pluns = pool.findall("./object[@type='Pool Public LUN']") + \
            pool.findall("./object[@type='Public RaidGroup LUN']") + \
            pool.findall("./object[@type='Private RaidGroup LUN']")
    if len(pluns) > 0:
        for plun in pluns:
            lname = plun.get('name')
            lunid = lunr.match(lname).group(2)
            lunname = lunr.match(lname).group(1)
            luns[ lunid ] = lunname
            lunpools += [ ( pname, lunid ) ]
    pdisks = pool.findall("./object[@type='Disk']")
    if len(pdisks) > 0:
        for disk in pdisks:
            dname = re.sub( " Disk ", "-", re.sub( " Enclosure ", "-", re.sub( "Bus ", "", disk.get('name') ) ) )
            disks.append(dname)
            diskpools += [ ( pname, dname ) ]

if tofile:
    out = open( outputfile, 'w' )
else:
    out = sys.stdout

out.write("graph \""+arrayname+"\" {\n")
out.write("  rankdir=LR;\n")
if compact:
    out.write("  splines=line;\n")

if compact:
    out.write("  hosts [ shape=record, label=\"")
    lh1 = len(hosts)-1
    for i in range(lh1):
        out.write("<"+re.sub("_","",re.sub("-","",hosts[i]))+"> "+hosts[i]+" | ")
    out.write("<"+re.sub("_","",re.sub("-","",hosts[lh1]))+"> "+hosts[lh1]+"\", style = \"filled\", fillcolor = \"ForestGreen\" ];\n")
else:
    for host in hosts:
        out.write("  \""+host+"\" [label = \""+host+"\", shape = \"square\", style = \"filled\", color = \"ForestGreen\"];\n")

if compact:
    out.write("  luns [ shape=record, label=\"")
    lk = list(luns.keys())
    ll1 = len(lk)-1
    for i in range(ll1):
        out.write("<"+lk[i]+"> "+lk[i]+": "+luns[lk[i]]+" | ")
    out.write("<"+lk[ll1]+"> "+lk[ll1]+": "+luns[lk[ll1]]+"\", style = \"filled\", fillcolor = \"SteelBlue\" ];\n")
else:
    for lun in luns.keys():
        out.write("  \""+lun+"\" [label = \""+lun+"\", style = \"filled\", color = \"SteelBlue\"];\n")

if compact:
    out.write("  pools [ shape=record, label=\"")
    lp1 = len(pools)-1
    for i in range(lp1):
        out.write("<"+re.sub(" ","",pools[i])+"> "+pools[i]+" | ")
    out.write("<"+re.sub(" ","",pools[lp1])+"> "+pools[lp1]+"\", style = \"filled\", fillcolor = \"SlateGray\" ];\n")
else:
    for pool in pools:
        out.write("  \""+pool+"\" [label = \""+pool+"\", shape = \"square\", style = \"filled\", color = \"SlateGray\"];\n")

if compact:
    out.write("  disks [ shape=record, label=\"")
    ld1 = len(disks)-1
    for i in range(ld1):
        out.write("<"+re.sub("-","",disks[i])+"> "+disks[i]+" | ")
    out.write("<"+re.sub("-","",disks[ld1])+"> "+disks[ld1]+"\", style = \"filled\", fillcolor = \"DarkGoldenrod\" ];\n")
else:
    out.write("{ rank = same;\n")
    for disk in disks:
        out.write("  \""+disk+"\" [label = \""+disk+"\", style = \"filled\", color = \"DarkGoldenrod\"];\n")

    out.write("};\n")

for lh in lunhosts:
    if compact:
        out.write("  hosts:"+re.sub("_","",re.sub("-","",lh[1]))+" -- luns:"+lh[0]+";\n")
    else:
        out.write("  \""+lh[1]+"\" -- \""+lh[0]+"\";\n")

for lp in lunpools:
    if compact:
        out.write("  luns:"+lp[1]+" -- pools:"+re.sub(" ","",lp[0])+";\n")
    else:
        out.write("  \""+lp[1]+"\" -- \""+lp[0]+"\";\n")

for pd in diskpools:
    if compact:
        out.write("  pools:"+re.sub(" ","",pd[0])+" -- disks:"+re.sub("-","",pd[1])+";\n")
    else:
        out.write("  \""+pd[0]+"\" -- \""+pd[1]+"\";\n")

out.write("}\n")
out.close()

