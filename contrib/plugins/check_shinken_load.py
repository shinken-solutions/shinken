#!/usr/bin/env python2
#
#   Autors: David Hannequin <david.hannequin@gmail.com>,
#           Hartmut Goebel <h.goebel@crazy-compilers.com>
#   Date: 2012-07-12
#
# Requires: Python >= 2.7 or Python plus argparse
#

import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--warning', default='3,2,1')
    parser.add_argument('-c', '--critical', default='4,3,2')
    args = parser.parse_args()

    critical = map(float, args.critical.split(','))
    warning = map(float, args.warning.split(','))

    (cload1, cload5, cload15) = critical
    (wload1, wload5, wload15) = warning

    (load1, load5, load15) = os.getloadavg()

    if load1 >= cload1 or load5 >= cload5 or load15 >= cload15:
        print ('CRITICAL - Load average : %s,%s,%s|load1=%s;load5=%s;load15=%s'
               % (load1, load5, load15, load1, load5, load15))
        raise SystemExit(2)
    elif load1 >= wload1 or load5 >= wload5 or load15 >= wload15:
        print ('WARNING - Load average : %s,%s,%s|load1=%s;load5=%s;load15=%s'
               % (load1, load5, load15, load1, load5, load15))
        raise SystemExit(1)
    else:
        print ('OK - Load average : %s,%s,%s|load1=%s;load5=%s;load15=%s'
               % (load1, load5, load15, load1, load5, load15))
        raise SystemExit(0)


if __name__ == "__main__":
    main()
