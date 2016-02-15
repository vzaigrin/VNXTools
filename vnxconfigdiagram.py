#
# Generate a description of configuration of EMC CLARiiON/VNX storage aray.
#
# It takes a configuration file extracted from an array by the command
#
# naviseccli arrayconfig -capture output arrayconfig.xml -o
#
# and generate a configuration diagram in a graphviz format.
#
# Copyright (c) 2015 Vadim Zaigrin <vzaigrin@yandex.ru>
#

import sys
import argparse
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

namespaces = { 'SAN':'http://emc.com/uem/schemas/Common_CLARiiON_SAN_schema',
               'CLAR':'http://emc.com/uem/schemas/Common_CLARiiON_schema'     }

tree = ET.parse( inputfile )
root = tree.getroot()

arrayname = root.find( ".//CLAR:CLARiiON/CLAR:Name",namespaces ).text
arraySN = root.find( ".//CLAR:CLARiiON/CLAR:SerialNumber", namespaces ).text
arrayModel = root.find( ".//CLAR:CLARiiON/CLAR:ModelNumber", namespaces ).text

hosts = set()
hbas = {}
for host in root.findall( ".//SAN:SAN/SAN:Servers/SAN:Server", namespaces ):
    hostname = host.find( "./SAN:HostName", namespaces ).text
    if not re.match( '^SP[AB]$', hostname ):
        hosts.add( hostname )
        for port in host.findall( ".//SAN:HBAPort", namespaces ):
            hbas[ port.find( "./SAN:WWN", namespaces ).text ] = hostname

hosts = list(hosts)
hosts.sort()

lunhost = []
for sg in root.findall( ".//CLAR:Logicals/CLAR:StorageGroups//CLAR:StorageGroup", namespaces ):
    sgluns = []
    for lun in sg.findall( "./CLAR:LUs//CLAR:LU/CLAR:ArrayNumber", namespaces ):
        sgluns += [ lun.text ]
    for wwn in sg.findall( "./CLAR:ConnectionPaths//CLAR:ConnectionPath/CLAR:ConnectedHBA/CLAR:WWN", namespaces ):
        for lun in sgluns:
            lunhost += [ ( lun, hbas.get(wwn.text) ) ]

lunhosts = set( lunhost )

disks = []
for disk in root.findall( ".//CLAR:Physicals/CLAR:Disks//CLAR:Disk", namespaces ):
    dname = disk.find( "./CLAR:Name", namespaces ).text
    dsize = disk.find( "./CLAR:CapacityInMBs", namespaces ).text
    if int(dsize) > 0:
        disks += [ re.sub( " Disk ", "-", re.sub( " Enclosure ", "-", re.sub( "Bus ", "", dname ))) ]

disks.sort()

rgs = set()
diskrgs = []
for rg in root.findall( ".//CLAR:Logicals/CLAR:RAIDGroups//CLAR:RAIDGroup", namespaces ):
    rgname = "RG " + rg.find( "./CLAR:ID", namespaces ).text
    rgisprivate = rg.find( "./CLAR:IsPrivate", namespaces ).text
    if not re.match( 'true', rgisprivate ):
        rgs.add( rgname )
        for disk in rg.findall( ".//CLAR:Disk/CLAR:Name", namespaces ):
            diskrgs += [ ( rgname, re.sub( " Disk ", "-", re.sub( " Enclosure ", "-", re.sub( "Bus ", "", disk.text ))) ) ]

pools = set()
diskpools = []
for dpool in root.findall( ".//CLAR:Logicals/CLAR:Diskpools//CLAR:Diskpool", namespaces ):
    pool = dpool.find( ".//CLAR:Pool/CLAR:Name", namespaces )
    if pool != None:
        poolname = pool.text
        pools.add( poolname )
        for disk in dpool.findall( ".//CLAR:Disk/CLAR:Name", namespaces ):
            diskpools += [ ( poolname, re.sub( " Disk ", "-", re.sub( " Enclosure ", "-", re.sub( "Bus ", "", disk.text ))) ) ]
 
pools = pools | rgs
pools = list(pools)
diskpools += diskrgs

lunsfromrg = {}
lunrgs = []
for lun in root.findall( ".//CLAR:Logicals/CLAR:LUNs//CLAR:LUN", namespaces ):
    lunid = lun.findall( "./CLAR:Number", namespaces )[0].text
    lunsfromrg[ lunid ] = lun.find( ".//CLAR:Name", namespaces ).text
    rgname = "RG " + lun.find( "./CLAR:RAIDGroupID", namespaces ).text
    lunrgs += [ ( rgname, lunid ) ]

lunsfrompool = {}
lunpools = []
for pool in root.findall( ".//CLAR:Logicals/CLAR:PoolProvisioning//CLAR:Pools//CLAR:Pool", namespaces ):
    poolname = pool.find( "./CLAR:Name", namespaces ).text
    for lun in pool.findall( "./CLAR:MLUs//CLAR:MLU", namespaces ):
        lunid = lun.find( "./CLAR:Number", namespaces ).text
        lunsfrompool[ lunid ] = lun.find( "./CLAR:Name", namespaces ).text
        lunpools += [ ( poolname, lunid ) ]

lunpools += lunrgs
luns = lunsfrompool.copy()
luns.update( lunsfromrg )

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

