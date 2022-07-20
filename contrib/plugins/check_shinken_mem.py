#!/usr/bin/env python
#
#   Autors: David Hannequin <david.hannequin@gmail.com>,
#           Hartmut Goebel <h.goebel@crazy-compilers.com>
#   Date: 2012-07-12
#
# Requires: Python >= 2.7 or Python plus argparse
# Platform: Linux
#

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse


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
    # :fixme: fails if one of these lines is missing in /proc/meminfo
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
