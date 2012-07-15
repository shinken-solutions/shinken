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
    """
    Read total mem, free mem and cached from /proc/meminfo

    This is linux-only.
    """
    for line in open('/proc/meminfo').readlines():
        if line.startswith('MemTotal:'):
            memTotal = line.split()[1]
        if line.startswith('MemFree:'):
            memFree = line.split()[1]
        if line.startswith('Cached:'):
            memCached = line.split()[1]
    return memTotal, memCached, memFree


def percentFreeMem():
    memTotal, memCached, memFree = MemValues()
    return (((int(memFree) + int(memCached)) * 100) / int(memTotal))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--warning', default='80', type=int)
    parser.add_argument('-c', '--critical', default='90', type=int)
    args = parser.parse_args()

    critical = args.critical
    warning = args.warning

    pmemUsage = 100 - percentFreeMem()

    if pmemUsage >= critical:
        print ('CRITICAL - Memory usage: %2.1f%% |mem=%s' % (pmemUsage, pmemUsage))
        raise SystemExit(2)
    elif pmemUsage >= warning:
        print ('WARNING - Memory usage: %2.1f%% |mem=%s' % (pmemUsage, pmemUsage))
        raise SystemExit(1)
    else:
        print ('OK - Memory usage: %2.1f%% |mem=%s' % (pmemUsage, pmemUsage))
        raise SystemExit(0)

if __name__ == "__main__":
    main()
