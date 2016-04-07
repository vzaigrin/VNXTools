"""
vnxfastvpreport.py - Reports EMC VNX pool LUNs distribution by FAST VP tiers

Requirements:
- Python 3.x
- naviseccli in the PATH
"""

from collections import OrderedDict
import argparse
import subprocess
import re
import csv
import time
import socket

# Parse command line options
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--address", required = True,
                    help = "VNX name or address")
parser.add_argument("-u", "--user", required=True, help = "username for VNX")
parser.add_argument("-p", "--password", required=True,
                    help = "password for VNX")
parser.add_argument("-s", "--scope", required=True,
                    help = "Scope option for VNX")
parser.add_argument("-l", "--long", help = "'long' output with capacity",
                    action = "store_true")
parser.add_argument("-o", "--output", help = "list of output formats " +
                    "separated by space: 'screen csv carbon html'",
                    nargs = '+', default = 'screen')
parser.add_argument("-f", "--filename", help = "filename for output",
                    default = "report")
parser.add_argument("-c", "--carbon", help = "carbon server name or address",
                    default = '127.0.0.1')
parser.add_argument("-t", "--port", type = int, help = "carbon server port",
                    default = 2003)
args = parser.parse_args()

# Prepare utility variables
rLun = re.compile(r'LOGICAL UNIT NUMBER ([0-9]+)')
rLunName = re.compile(r'Name: (.*)')
rPool = re.compile(r'Pool Name: (.*)')
rCapacityUser = re.compile(r'User Capacity \(GBs\): ')
rCapacityConsumed = re.compile(r'Consumed Capacity \(GBs\): ')
rMetadata = re.compile(r'Metadata Allocation \(GBs\): ')
rTierExtreme = re.compile(r'Extreme Performance: ')
rTierPerformance = re.compile(r'Performance: ')
rTierCapacity = re.compile(r'Capacity: ')

metaHeaders = [ 'pool', 'lun', 'lunName' ]
headers = OrderedDict()
headers['pool'] = 'Pool'
headers['lun'] = 'LUN'
headers['lunName'] = 'Name'
headers['tierExtreme'] = 'Extreme'
headers['tierPerformance'] = 'Performance'
headers['tierCapacity'] = 'Capacity'

if args.long:
    headers['capacityUser'] = 'User'
    headers['capacityConsumed'] = 'Consumed'
    headers['metadata'] = 'Metadata'

# Run naviseccli
navi = "naviseccli -User " + args.user + " -Password " + args.password + \
       " -Scope " + args.scope + " -Address " + args.address + \
       " lun -list -poolName -tiers -userCap -consumedCap -metadataAllocation"

cmd = subprocess.Popen( navi, shell = True, stdout = subprocess.PIPE,
                        universal_newlines = True )

# Parse naviseccli output
data = []
lunData = OrderedDict()
lun = ""
lunName = ""
pool = ""
capacityUser = 0.0
capacityConsumed = 0.0
metadata = 0.0
tierExtreme = 0.0
tierPerformance = 0.0
tierCapacity = 0.0
firstLun = True

for line in cmd.stdout:
    if rLun.match(line):
        if not firstLun:
            data.append(lunData)
        lunData = OrderedDict()
        lunData['pool'] = ""
        lunData['lun'] = int(rLun.match(line).group(1))
        lunData['lunName'] = ""
        lunData['tierExtreme'] = 0.0
        lunData['tierPerformance'] = 0.0
        lunData['tierCapacity'] = 0.0
        lunData['capacityUser'] = 0.0
        lunData['capacityConsumed'] = 0.0
        lunData['metadata'] = 0.0
        firstLun = False

    if rLunName.match(line):
        lunData['lunName'] = rLunName.match(line).group(1)
    if rPool.match(line):
        lunData['pool'] = rPool.match(line).group(1)
    if rCapacityUser.match(line):
        lunData['capacityUser'] = float(re.findall(r'\d+\.\d+', line)[0])
    if rCapacityConsumed.match(line):
        lunData['capacityConsumed'] = float(re.findall(r'\d+\.\d+', line)[0])
    if rMetadata.match(line):
        lunData['metadata'] = float(re.findall(r'\d+\.\d+', line)[0])
    if rTierExtreme.match(line):
        lunData['tierExtreme'] = float(re.findall(r'\d+\.\d+', line)[0])
    if rTierPerformance.match(line):
        lunData['tierPerformance'] = float(re.findall(r'\d+\.\d+', line)[0])
    if rTierCapacity.match(line):
        lunData['tierCapacity'] = float(re.findall(r'\d+\.\d+', line)[0])

if not firstLun:
    data.append(lunData)

if len(data) == 0:
    print("No data from the Naviseccli output")
    exit(-1)

pools = sorted(set([d['pool'] for d in data]))

# Output to the screen
if "screen" in args.output:
    wide = OrderedDict()
    for key in headers:
        wide[key] = len(headers[key])

    for d in data:
        for key in headers.keys():
            if len(str(d[key])) > wide[key]:
                wide[key] = len(str(d[key]))

    for key in headers.keys():
        print(headers[key].rjust(wide[key]), " ", end='')
    print()

    for pool in pools:
        poolData = [d for d in data if d['pool'] == pool]
        poolData = sorted(poolData, key = lambda k: k['lun'])
        for ld in poolData:
            for key in headers.keys():
                print(str(ld[key]).rjust(wide[key]), " ", end = '')
            print()

# Output into csv file
if "csv" in args.output:
    filename = args.filename + ".csv"
    fieldnames = list(headers.keys())
    csvfile = open(filename, 'w', newline = '')
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames,
                            extrasaction='ignore')
    writer.writerow(headers)
    for pool in pools:
        poolData = [d for d in data if d['pool'] == pool]
        poolData = sorted(poolData, key = lambda k: k['lun'])
        for ld in poolData:
            writer.writerow(ld)
    csvfile.close()

# Output to carbon (graphite) server
if "carbon" in args.output:
    epoch_time = int(time.time())
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((args.carbon, args.port))
    fieldnames = list(headers.keys())
    for field in metaHeaders:
        fieldnames.remove(field)
    for pool in pools:
        poolID = pool.replace(" ", "").replace(".", "_")
        for d in [d for d in data if d['pool'] == pool]:
            for key in fieldnames:
                s.sendall(str.encode("vnx." + args.address.replace(".", "_") +
                                     ".block.fastvp." + poolID + "." +
                                     str(d['lun']) + "." + key + " " +
                                     str(d[key]) + " " + str(epoch_time) + "\n"))
    s.close()

# Output into html file with diagrams
if "html" in args.output:
    filename = args.filename + ".html"
    f = open(filename, 'wt')
    print("<head>", file = f)
    print("<meta charset='utf-8'>", file = f)
    print("<!-- saved from url=(0014)about:internet -->", file = f)
    print("<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>",
          file = f)
    print("</head>", file = f)
    print("<body>", file = f)
    print("<h1><center>" + args.address + "</center></h1>", file = f)

    for pool in pools:
        poolID = pool.replace(" ", "")
        poolData = [d for d in data if d['pool'] == pool]
        poolData = sorted(poolData, key = lambda k: k['lun'])
        print("<div id='" + poolID + "' " +
              "style = 'width: 800px; height: 600px;'></div>",
              file = f)
        print("<script>", file = f)

        print("var " + poolID + "trace1 = {", file = f)
        print("x: [ ", end ='', file = f)
        for ld in poolData:
            print("'" + ld['lunName'] + "', ", end = '', file = f)
        print(" ],", file = f)
        print("y: [ ", end ='', file = f)
        for ld in poolData:
            print(ld['tierCapacity'], ", ", end = '', file = f)
        print(" ],", file = f)
        print("name: 'Capacity',", file = f)
        print("type: 'bar'", file = f)
        print("};", file = f)

        print("var " + poolID + "trace2 = {", file = f)
        print("x: [ ", end ='', file = f)
        for ld in poolData:
            print("'" + ld['lunName'] + "', ", end = '', file = f)
        print(" ],", file = f)
        print("y: [ ", end ='', file = f)
        for ld in poolData:
            print(ld['tierPerformance'], ", ", end = '', file = f)
        print(" ],", file = f)
        print("name: 'Performance',", file = f)
        print("type: 'bar'", file = f)
        print("};", file = f)

        print("var " + poolID + "trace3 = {", file = f)
        print("x: [ ", end ='', file = f)
        for ld in poolData:
            print("'" + ld['lunName'] + "', ", end = '', file = f)
        print(" ],", file = f)
        print("y: [ ", end ='', file = f)
        for ld in poolData:
            print(ld['tierExtreme'], ", ", end = '', file = f)
        print(" ],", file = f)
        print("name: 'Extreme',", file = f)
        print("type: 'bar'", file = f)
        print("};", file = f)

        print("var " + poolID + "data = [" + poolID + "trace1, " +
              poolID + "trace2, " + poolID + "trace3];", file = f)
        print("var layout = { title: '" + pool + "', barmode: 'stack'};",
              file = f)
        print("Plotly.newPlot('" + poolID + "', " + poolID +
              "data, layout);", file = f)
        print("</script>", file = f)

    print("</body>", file = f)
    f.close()

