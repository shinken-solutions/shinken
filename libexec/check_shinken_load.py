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
    print sys.argv[0] + ' -w <load1,load5,load15> -c <load1,load5,load15>'
    print '   -c (--critical)      Three critical tresholds (defaults : 4,3,2)\n';
    print '   -w (--warning)       Three warning tresholds (defaults : 3,2,1)\n';
    print '   -h (--help)          Usage help\n';
#
# Main
#

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

if __name__ == "__main__":
    main()
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--warning', default = '3,2,1')
    parser.add_argument('-c', '--critical', default = '4,3,2' )
    args = parser.parse_args()
    critical = args.critical
    warning = args.warning
    
    (d1, d2, d3) = os.getloadavg()

    load1 = str(d1)
    load5 = str(d2)
    load15 = str(d3)
    
    listcritical = critical.split(',') 
    listwarning = warning.split(',') 
	
    cload1 = str(listcritical[0]) 
    cload5 = str(listcritical[1]) 
    cload15 = str(listcritical[2]) 

    wload1 = str(listwarning[0])
    wload5 = str(listwarning[1])
    wload15 = str(listwarning[2])
    

    if load1 >= cload1 or load5 >= cload5 or load15 >= cload15 : 
       print 'CRITICAL - Load average : '+load1+','+load5+','+load15+'|load1='+load1+'; load5='+load5+'; load15='+load15    
       sys.exit(2)
    elif load1 >= wload1 or load5 >= wload5 or load15 >= wload15 :  
       print 'WARNING - Load average : '+load1+','+load5+','+load15+'|load1='+load1+'; load5='+load5+'; load15='+load15    
       sys.exit(1)
    else :
       print 'OK - Load average : '+load1+','+load5+','+load15+'|load1='+load1+'; load5='+load5+'; load15='+load15    
       sys.exit(0)

