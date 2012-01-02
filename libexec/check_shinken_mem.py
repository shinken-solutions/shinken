#!/usr/bin/env python
#   Autor : David Hannequin <david.hannequin@gmail.com>
#   Date : 29 Nov 2011

#
# Script init
#

import sys
import os
import argparse
import getopt 

#
# Usage 
#

def usage():
    print 'Usage :'
    print sys.argv[0] + ' -w <80> -c <90>'
    print '   -c (--critical)      Critical tresholds (defaults : 90%)\n';
    print '   -w (--warning)       Warning tresholds (defaults : 80%)\n';
    print '   -h (--help)          Usage help\n';

#
# Main
#

def readLines(filename): 
    f = open(filename, "r") 
    lines = f.readlines() 
    return lines 

def MemValues():
    global memTotal, memCached, memFree
    for line in readLines('/proc/meminfo'):
        if line.split()[0] == 'MemTotal:':
            memTotal = line.split()[1]
        if line.split()[0] == 'MemFree:':
            memFree = line.split()[1]
        if line.split()[0] == 'Cached:':
             memCached = line.split()[1]

def percentMem():                                                                                                                                             
    MemValues()
    return (((int(memFree) + int(memCached)) * 100) / int(memTotal))  

def main():

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hwc:v", ["help", "warning", "critical"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err) 
        usage()
        sys.exit(2)
    output = None
    verbose = False

    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-w", "--warning"):
            notification = a
        elif o in ("-c", "--critical"):
            notification = a
	else :
	    assert False , "unknown options"

    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--warning', default = '80')
    parser.add_argument('-c', '--critical', default = '90' )
    args = parser.parse_args()
    critical = args.critical
    warning = args.warning
    cmem = str(critical) 
    wmem = str(warning)
    pmemFree = percentMem()
    pmemUsage = 100 - pmemFree 
    pmemUsage = str(pmemUsage)
 
    if pmemUsage >= cmem : 
       print 'CRITICAL - Memory usage : '+pmemUsage+'% |mem='+pmemUsage   
       sys.exit(2)
    elif pmemUsage >= wmem :
       print 'WARNING - Memory usage : '+pmemUsage+'% |mem='+pmemUsage    
       sys.exit(1)
    else :
       print 'OK - Memory usage : '+pmemUsage+'% |mem='+pmemUsage   
       sys.exit(0)

if __name__ == "__main__":
    main()
