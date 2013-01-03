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
import math
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
import pymongo
import math
import optparse
import gzip



try:
    from shinken.bin import VERSION
    import shinken
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    imp.load_module('shinken', *imp.find_module('shinken', [os.path.realpath("../.."), os.path.realpath("../../.."), os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "..")]))

from shinken.trending.trender import Trender
from shinken.load import Load
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


# 15min chunks
CHUNK_INTERVAL = 3600
nb_chunks = int(math.ceil(86400.0/CHUNK_INTERVAL))

trender = Trender(CHUNK_INTERVAL)

# Monday = 0
for i in range(0, 7):
    datas[i] = [None for j in range(0, nb_chunks)]
    raw_datas[i] = [None for j in range(0, nb_chunks)]



#nb_chunks = 86400/CHUNK_INTERVAL
_times = range(0, nb_chunks*len(datas))


# By deault no debug messages
do_debug = False

def debug(*args):
    if do_debug:
        print ' '.join([str(s) for s in args])
        

def open_connexion():
    global con, coll
    # SAFE IS VERY VERY important!
    con = pymongo.Connection('localhost', safe=True)
    coll = con.shinken.trending
    debug("Connexion open with", coll)


def open_csv(path):
    # Ok reopen it with
    if path.endswith('.gz'):
        debug('Opening gzip file', path)
        f = gzip.open(path, 'rb')
    else:
        debug('Opening standard file', path)
        f = open(path, 'rb')
    reader = csv.reader(f, delimiter=';')
    return reader


def import_csv(reader, _hname, _sdesc, _metric):
    global hname, sdesc, metric
    i = 0
    for row in reader:
        if i == 0:
            # Maybe the first line is an helper line, if so,
            # use it
            if len(row) == 3 and row[0].startswith('#'):
                hname = row[0][1:]
                sdesc = row[1]
                metric = row[2]
            print "IMPORTANT : Removing all entries from ", coll, "for the metric", hname, sdesc, metric
            coll.remove({'hname':hname, 'sdesc':sdesc, 'metric':metric})
            i += 1
            _hname = hname
            _sdesc = sdesc
            _metric = metric
        try:
            _time = int(row[0])
        except ValueError:
            continue
        try:
            l1   = float(row[1])
        except (IndexError, ValueError):
            continue

        # If here we still do not have valid entries, we are not good at all!
        if not hname or not sdesc or not metric:
            print "ERROR : missing hostname, or service description or metric name, please check your input file or fill the values as arguments"
            sys.exit(2)

        sec_from_morning = get_sec_from_morning(_time)
        wday = get_wday(_time)
    
        chunk_nb = sec_from_morning / CHUNK_INTERVAL

        # Now update mongodb
        trender.update_avg(coll, _time, wday, chunk_nb, l1, _hname, _sdesc, _metric, CHUNK_INTERVAL)



def get_regexp_param(fil):
    if do_regexp:
        return {'$regex':fil}
    else:
        return fil



# Smooth a list with our average and return the new list smoothed
def smooth_list(l):
    res = []
    cur_l = None
    for v in l:
        if not cur_l:
            cur_l = Load(m=1, initial_value=v)
        cur_l.update_load(v, 5)
        res.append(cur_l.get_load())
    return res




def get_graph_values(hname, sdesc, metric, mkey):
    _from_mongo = []
    for wday in range(0, 7):
        for chunk_nb in range(nb_chunks):            
            key = trender.get_key(hname, sdesc, metric, wday, chunk_nb)#hname+sdesc+metric+'week'+str(wday)+'Vtrend'+str(chunk_nb)
            doc = coll.find_one({'_id':key})
            if doc:
                _from_mongo.append(doc[mkey])
            else:
                debug("Warning : no db entry for", key)
                prev_wday, prev_chunk_nb = trender.get_previous_chunk(wday, chunk_nb)
                key = trender.get_key(hname, sdesc, metric, prev_wday, prev_chunk_nb)#hname+sdesc+metric+'week'+str(prev_wday)+'Vtrend'+str(prev_chunk_nb)
                doc = coll.find_one({'_id':key})
                if doc:
                    _from_mongo.append(doc[mkey])
                else:
                    debug("Warning : ok really no possible entry for", key)
                    _from_mongo.append(-1)

    return _from_mongo







if __name__ == '__main__':
    parser = optparse.OptionParser(
        "%prog [options]", version="%prog " + '0.1')
    parser.add_option('-c', '--csv',
                      dest="csv_file",
                      help='Import a CSV file')
    parser.add_option('-H', '--host_name',
                      dest="host_name",
                      help="Hostname of the imported data")
    parser.add_option('-s', '--service_description',
                      dest="service_description",
                      help="Service description of the imported data")
    parser.add_option('-m', '--metric', dest='metric',
                      help="Metric name of the imported data")
    parser.add_option('-p', '--print',
                      dest='do_print', action='store_true',
                      help='Print the loaded trending')
    parser.add_option('-d', '--debug',
                      dest='do_debug', action='store_true',
                      help='Enable debug output')
    parser.add_option('--projection',
                      dest='projection',
                      help='Number of weeks to show, by default 1. If >=2 will show the trending prevision over theses weeks.')
    parser.add_option('--delete',
                      dest='do_delete', action='store_true',
                      help='Delete the values for the metric')
    parser.add_option('-l', '--list',
                      dest='do_list', action='store_true',
                      help='List all metrics for an host or a service in the database')
    parser.add_option('-r', '--regexp',
                      dest='do_regexp', action='store_true',
                      help='Enable regexp in listing and removing of metrics')
    
    if len(sys.argv) == 1:
        sys.argv.append('-h')
    
    opts, args = parser.parse_args()

    
    do_debug  = opts.do_debug
    do_delete = opts.do_delete
    do_list   = opts.do_list
    do_regexp = opts.do_regexp
    
    # ok open the connexion
    open_connexion()
    

    hname = opts.host_name
    sdesc = opts.service_description
    metric = opts.metric
    do_print = opts.do_print
    csv_file = opts.csv_file
    projection = int(opts.projection or '1')

    if do_print and plt is None:
        print "ERROR : cannot import matplotlib, please install it"
        sys.exit(2)
        

    if csv_file:
        reader = open_csv(csv_file)
        import_csv(reader, hname, sdesc, metric)

    if do_print:    
        _from_mongo = get_graph_values(hname, sdesc, metric, 'VtrendSmooth')
        _from_mongo_short = get_graph_values(hname, sdesc, metric, 'VcurrentSmooth')
        _el_raw = get_graph_values(hname, sdesc, metric, 'Vcurrent')
        _el_evolution = get_graph_values(hname, sdesc, metric, 'VevolutionSmooth')

        pct_failed = 0.0
        for i in xrange(len(_from_mongo)):
            try:
                pct_failed += abs(_from_mongo_short[i] - _from_mongo[i]) / _from_mongo[i]
            except ZeroDivisionError:
                pass
            except IndexError:
                print "Was trying to get", i
            except TypeError:
                print "Was trying to get", i
        pct_failed /= len(_from_mongo)
        debug("pct_failed MONGO:", pct_failed)

        projections = []
        _long_times = []
        if projection > 1:
            
            for wnb in range(1, projection):
                for i in xrange(len(_from_mongo)):
                    trend = _from_mongo[i]
                    evol  = _el_evolution[i]
                    proj_value = trend + wnb*evol
                    projections.append(proj_value)
                    _long_times.append( wnb  * len(_from_mongo) + i)

        if csv_file:
            plt.plot(_from_mongo, 'r',  _times, _el_evolution, 'b',_long_times, projections, 'y')
            plt.show()
        else:
            plt.plot(_times, _from_mongo, 'r', _times, _from_mongo_short, 'y', _times, _el_evolution, 'b', _long_times, projections, 'c')
            plt.show()
            

    if do_delete:
        d = None
        if hname and not sdesc and not metric:
            print "Removing the entries for", hname
            d = {'hname':get_regexp_param(hname)}
        if hname and sdesc and not metric:
            print "Removing the entries for", hname, sdesc
            d = {'hname':get_regexp_param(hname), 'sdesc':get_regexp_param(sdesc)}
        if hname and sdesc and metric:
            print "Removing the entries for", hname, sdesc, metric
            d = {'hname':get_regexp_param(hname), 'sdesc':get_regexp_param(sdesc), 'metric':get_regexp_param(metric)}
        if d:
            coll.remove(d)
            print "Done"



    if do_list:
        if not hname and not sdesc:
            r = coll.find({}, {'hname':1}).distinct('hname')
            hosts = [e for e in r]
            hosts.sort()
            for h in hosts:
                print h
        

        if hname and not sdesc:
            r = coll.find({'hname': get_regexp_param(hname)}, {'sdesc':1}).distinct('sdesc')
            services = [e for e in r]
            services.sort()
            for s in services:
                print s

        if hname and sdesc:
            r = coll.find({'hname': hname, 'sdesc': get_regexp_param(sdesc)}, {'metric':1}).distinct('metric')
            metrics = [e for e in r]
            metrics.sort()
            for m in metrics:
                print m
