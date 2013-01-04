#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

import os
import csv
import time
import sys
import pymongo
import optparse



try:
    from shinken.bin import VERSION
    import shinken
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    imp.load_module('shinken', *imp.find_module('shinken', [os.path.realpath("../.."), os.path.realpath("../../.."), os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "../..")]))

from shinken.trending.trender import Trender
from shinken.util import get_sec_from_morning, get_wday

# Somre Global var
# (we are in a script, so it's ok)

con = None
coll = None
reader = None
datas = {}
raw_datas = {}

do_regexp = False
hname = None
sdesc = None
metric = None



trender = None


# By deault no debug messages
do_debug = False

def debug(*args):
    if do_debug:
        print ' '.join([str(s) for s in args])
        

def open_connexion(uri):
    global con, coll
    con = pymongo.Connection(uri)
    coll = con.shinken.trending
    debug("Connexion open with", coll)




def get_regexp_param(fil):
    if do_regexp:
        return {'$regex':fil}
    else:
        return fil



def get_graph_value(hname, sdesc, metric, wday, chunk_nb):
    key = trender.get_key(hname, sdesc, metric, wday, chunk_nb)
    doc = coll.find_one({'_id':key})
    return doc





if __name__ == '__main__':
    parser = optparse.OptionParser(
        "%prog [options]", version="%prog " + '0.1')
    parser.add_option('--chunk-size',
                      dest="chunk_interval",
                      help='Size of the chunk size')
    parser.add_option('-H', '--host_name',
                      dest="host_name",
                      help="Hostname of the imported data")
    parser.add_option('-s', '--service_description',
                      dest="service_description",
                      help="Service description of the imported data")
    parser.add_option('-m', '--metric', dest='metric',
                      help="Metric name of the imported data")
    parser.add_option('-p', '--perfdata',
                      dest='perfdata',
                      help='Perfdata output to read metric names from')
    parser.add_option('--prevision',
                      dest='prevision',
                      help='Number of weeks to look in the future. By default 0 (means now)')
    parser.add_option('-r', '--regexp',
                      dest='do_regexp', action='store_true',
                      help='Enable regexp in metric get. Will take the first available')
    parser.add_option('-t', '--check-time',
                      dest='check_time',
                      help='Check time of the perfdata to look at. If unset, use now')
    parser.add_option('-W', '--warning',
                      dest='warning',
                      help='Warning percent band (top and low). Outside is warning.')
    parser.add_option('-C', '--critical',
                      dest='critical',
                      help='Critical percent band (top and low). Outside is critical.')
    parser.add_option('-U', '--uri',
                      dest='uri',
                      help='Mongodb URI to connect from')
    
    
    if len(sys.argv) == 1:
        sys.argv.append('-h')
    
    opts, args = parser.parse_args()

    
    do_regexp = opts.do_regexp
    uri = opts.uri or 'localhost'
    
    # ok open the connexion
    open_connexion(uri)


    CHUNK_INTERVAL = int(opts.chunk_interval or '300')
    trender = Trender(CHUNK_INTERVAL)

    hname = opts.host_name
    sdesc = opts.service_description
    metric = opts.metric
    prevision = int(opts.prevision or '0')
    check_time = int(opts.check_time or time.time())
    
    sec_from_morning = get_sec_from_morning(check_time)
    wday = get_wday(check_time)
    chunk_nb = sec_from_morning / CHUNK_INTERVAL

    warning = opts.warning or '20%'
    critical = opts.critical or '50%'

    if warning.endswith('%'):
        warning = warning[:-1]
    warning = int(warning)
    if critical.endswith('%'):
        critical = critical[:-1]
    critical = int(critical)

    if not hname and not sdesc:
        print "Missing host name and service description options (-H and -s), please fill them"
        sys.exit(2)

    
    doc = get_graph_value(hname, sdesc, metric, wday, chunk_nb)
    #print "GOT DOC", doc

    last_update = doc['last_update']
    oldiness = check_time - last_update
    if last_update < check_time - CHUNK_INTERVAL:
        print "Unknown : the database is too old to be valid, please look at your trending module"
        sys.exit(3)

    VtrendSmooth = doc['VtrendSmooth']
    VcurrentSmooth = doc['VcurrentSmooth']
    VevolutionSmooth = doc['VevolutionSmooth']

    #print VcurrentSmooth, 'will be compared to', VtrendSmooth
    #print "With the warning/critical pct", warning, critical

    s_perf = 'trend=%.2f current=%.2f' % (VtrendSmooth, VcurrentSmooth)

    if VtrendSmooth == 0 and VcurrentSmooth != 0:
        print "Unknown : the current value is not zero when the trending is, cannot compare with percent | %s" % s_perf
        sys.exit(3)

    # Ok manae the both 0 cases
    if VtrendSmooth == VcurrentSmooth:
        print "OK : values are equal | %s" % s_perf

    pct_diff = float(100 * (VcurrentSmooth - VtrendSmooth) / VtrendSmooth)
    #print "PCT diff", pct_diff

    s_perf += ' variation=%.2f%%' % pct_diff

    abs_pct_diff = abs(pct_diff)

    rc = 0

    if abs_pct_diff > warning:
        rc = 1

    if abs_pct_diff > critical:
        rc = 2

    if rc == 0:
        print "OK : current variation (%d%%) is within the limits | %s" % (pct_diff, s_perf)

    if rc == 1:
        print "Warning : current variation (%d%%) is in the warning band| %s" % (pct_diff, s_perf)

    if rc == 2:
        print "Critical : current varitation (%d%%) is in the critical band! | %s" % (pct_diff, s_perf)

    if rc == 3:
        print "Unknown : the current value cannot be compared with the reference | %s" % (pct_diff, s_perf)

    sys.exit(rc)
