#!/usr/bin/env python
#   Autor: David Hannequin <david.hannequin@gmail.com>
#   Date: 29 Nov 2011

#
# Script init
#

import sys
import os
import argparse

#



def MemValues():
    global memTotal, memCached, memFree
    for line in open('/proc/meminfo').readlines():
        if line.startswith('MemTotal:'):
            memTotal = line.split()[1]
        if line.startswith('MemFree:'):
            memFree = line.split()[1]
        if line.startswith('Cached:'):
            memCached = line.split()[1]


def percentMem():
    MemValues()
    return (((int(memFree) + int(memCached)) * 100) / int(memTotal))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--warning', default='80')
    parser.add_argument('-c', '--critical', default='90')
    args = parser.parse_args()
    critical = args.critical
    warning = args.warning
    cmem = str(critical)
    wmem = str(warning)
    pmemFree = percentMem()
    pmemUsage = 100 - pmemFree
    pmemUsage = str(pmemUsage)

    if pmemUsage >= cmem:
        print ('CRITICAL - Memory usage: %2.1f%% |mem=%s' % (pmemUsage, pmemUsage))
        raise SystemExit(2)
    elif pmemUsage >= wmem:
        print ('WARNING - Memory usage: %2.1f%% |mem=%s' % (pmemUsage, pmemUsage))
        raise SystemExit(1)
    else:
        print ('OK - Memory usage: %2.1f%% |mem=%s' % (pmemUsage, pmemUsage))
        raise SystemExit(0)

if __name__ == "__main__":
    main()
