#!/usr/bin/env python3

import re
from subprocess import call

#indexFile='/home/www/mirrors/index.html'
#statusFile='/home/root/Mirrors/Scripts/syncStatus.log'
indexFile='/home/husixu/index.html'
statusFile='/home/husixu/syncStatus.log'

startFlag = r"<!-- START OF THE TABLE -->"
endFlag = r"<!-- END OF THE TABLE -->"

ret = call(["cp", indexFile, indexFile+".bak"])
if ret:
    print("cannot make backup, exiting ...")
    exit(0);

with open(indexFile, 'r') as indexHtml:
    allLines = indexHtml.readlines()
    indexHtml.readlines
    indexHtml.close

startIndex = 0
endIndex = 0

# find the start and end segment
temp=0
segmentFinder=re.compile(startFlag)
for line in allLines:
    temp = temp + 1
    if segmentFinder.search(line):
        startIndex = temp
        break

temp=0
segmentFinder=re.compile(endFlag)
for line in allLines:
    temp = temp + 1
    if segmentFinder.search(line):
        endIndex = temp
        break

# substitute the repo status
sectionFinder=re.compile(r"<tr>")
itemFinder = re.compile(r"<td>")
with open(statusFile, 'r') as statusFile:
    statusLines = statusFile.readlines()
    statusLines.reverse()       # new lines first

    index = 0
    if startIndex and endIndex:
        while index < endIndex:
            # find the section
            while not sectionFinder.search(allLines[index]) and index < endIndex:
                index = index + 1
            if index == endIndex:
                break

            # first item, name
            while not itemFinder.search(allLines[index]) and index < endIndex:
                index = index + 1
            if index == endIndex:
                break

            name = re.search(r"href\s*=\s*\"\s*([\w_\-]+)\s*\"",allLines[index]).group(1)
            # find line in satus line
            statusLine = None
            for statusLine in statusLines:
                if re.search(r"^"+name,statusLine):
                    syncStatus= re.search(r"^[\w_\-\.]+\s+(\w+)\s+",statusLine).group(1)
                    syncTime = re.search(r"\d+-\d+-\d+_\d+:\d+:\d+",statusLine).group(0)
                    break

            # second item, sync time
            index = index + 1
            while not itemFinder.search(allLines[index]) and index < endIndex:
                index = index + 1
            if index == endIndex:
                break

            allLines[index] = "<td>"+syncTime+"</td>\n"

            index = index + 1
            while not itemFinder.search(allLines[index]) and index < endIndex:
                index = index + 1
            if index == endIndex:
                break

            allLines[index] = "<td>"+syncStatus+"</td>\n"

with open(indexFile,'w') as indexHtml:
    indexHtml.writelines(allLines)
    indexHtml.close()

