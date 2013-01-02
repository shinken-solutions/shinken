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



# Somre Global var
# (we are in a script, so it's ok)

con = None
coll = None
reader = None
datas = {}
raw_datas = {}

hname = None
sdesc = None
metric = None

# 15min chunks
CHUNK_INTERVAL = 900
nb_chunks = int(math.ceil(86400.0/CHUNK_INTERVAL))

# Monday = 0
for i in range(0, 7):
    #print "CREATING DAY", i
    #print "SHOULD CREATE", nb_chunks, "values by day"
    datas[i] = [None for j in range(0, nb_chunks)]
    raw_datas[i] = [None for j in range(0, nb_chunks)]



#nb_chunks = 86400/CHUNK_INTERVAL
_times = range(0, nb_chunks*len(datas))

_t = []
ultra_raw = []
_raw_t = []


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

    


class Load:
    def __init__(self, m=1, initial_value=0):
        self.exp = 0  # first exp
        self.m = m  # Number of minute of the avg
        self.val = initial_value  # first value
        self.nb_update = 1
        

    def update_load(self, new_val, interval):
        try:
            diff = interval
            self.exp = 1 / math.exp(diff / (self.m * 60.0))
            self.val = new_val + self.exp * (self.val - new_val)
        except OverflowError:  # if the time change without notice, we overflow :(
            pass
        except ZeroDivisionError:  # do not care
            pass
        
        
        #self.val += new_val
        #self.nb_update += 1

    def get_load(self):
        return self.val# / self.nb_update


def quick_update(prev_val, new_val, m, interval):
    l = Load(m=m, initial_value=prev_val)
    l.update_load(new_val, interval)
    return l.get_load()



def get_sec_from_morning(t):
    t_lt = time.localtime(t)
    h = t_lt.tm_hour
    m = t_lt.tm_min
    s = t_lt.tm_sec
    return h * 3600 + m * 60 + s


def get_wday(t):
    t_lt = time.localtime(t)
    return  t_lt.tm_wday


def get_day(t):
    return int(t - get_sec_from_morning(t))


def get_start_of_day(year, month_id, day):
    start_time = (year, month_id, day, 00, 00, 00, 0, 0, -1)
    try:
        start_time_epoch = time.mktime(start_time)
    except OverflowError:
        # Windows mktime sometimes crashes on (1970, 1, 1, ...)
        start_time_epoch = 0.0
    
    return start_time_epoch


def get_previous_chunk(wday, chunk_nb):
    if chunk_nb == 0:
        chunk_nb = nb_chunks - 1
        wday -= 1
    else:
        chunk_nb -= 1
    wday = wday % 7
    return (wday, chunk_nb)
                                                                


def get_key(hname, sdesc, metric, wday, chunk_nb):
    return hname+'.'+sdesc+'.'+metric+'.'+'week'+'.'+str(wday)+'.'+'Vtrend'+'.'+str(chunk_nb)


def update_avg(wday, chunk_nb, l1, hname, sdesc, metric):
    key = get_key(hname, sdesc, metric, wday, chunk_nb)#hname+'.'+sdesc+'.'+metric+'.'+'week'+'.'+str(wday)+'.'+'Vtrend'+'.'+str(chunk_nb)
    doc = coll.find_one({'_id' : key})
    if not doc:
        doc = {'hname':hname, 'sdesc':sdesc, 'metric':metric, 'cycle':'week',
               'wday':wday, 'chunk_nb':chunk_nb, 'Vtrend':l1, '_id':key,
               'VtrendSmooth':l1, 'VcurrentSmooth':l1, 'Vcurrent':l1
               }
        coll.save(doc)
    else:
        prev_val = doc['Vtrend']
        
        new_Vtrend = quick_update(prev_val, l1, 5, 5)
        
        # Now we smooth with the last value
        # And by default, we are using the current value
        new_VtrendSmooth = doc['VtrendSmooth']

        prev_doc = None
        cur_wday = wday
        cur_chunk_nb = chunk_nb
        # Ok by default take the current avg
        prev_val = doc['VtrendSmooth']
        prev_val_short = doc['VcurrentSmooth']
        
        cur_wday, cur_chunk_nb = get_previous_chunk(cur_wday, cur_chunk_nb)
        prev_key = get_key(hname, sdesc, metric, cur_wday, cur_chunk_nb)#hname+'.'+sdesc+'.'metric+'.'+'week'+str(cur_wday)+'.'+'Vtrend'+str(cur_chunk_nb)
        prev_doc = coll.find_one({'_id' : prev_key})
        if prev_doc:
            prev_val = prev_doc['VtrendSmooth']
            prev_val_short = prev_doc['VcurrentSmooth']
        else:
            debug("OUPS, the key", key, "do not have a previous entry", cur_wday, cur_chunk_nb)

        # Ok really update the value now
        new_VtrendSmooth = quick_update(prev_val, new_Vtrend, 1, 5)

        # Ok and now last minutes trending
        new_VcurrentSmooth = quick_update(prev_val_short, l1, 1, 15)
        
        coll.update({'_id' : key}, {'$set' : { 'Vtrend': new_Vtrend, 'VtrendSmooth': new_VtrendSmooth, 'VcurrentSmooth' : new_VcurrentSmooth, 'Vcurrent':l1  }})


def update_in_memory(wday, chunk_nb, l1):
    day = datas[wday]
    ld = day[chunk_nb]

    # Update the raw_data for this day
    raw_day = raw_datas[wday]
    #if not raw_day[chunk_nb]:
    raw_day[chunk_nb] = l1
    
    #print "Current ld", ld
    if not ld:
        #print "NEW"* 20, chunk_nb
        ld = Load(m=5, initial_value=l1)
        day[chunk_nb] = ld        
    else:
        # WAS 5
        ld.update_load(l1, 5)



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
        except IndexError:
            continue
        except ValueError:
            continue
        sec_from_morning = get_sec_from_morning(_time)
        wday = get_wday(_time)
    
        chunk_nb = sec_from_morning / CHUNK_INTERVAL

        update_in_memory(wday, chunk_nb, l1)

        # Now update mongodb
        update_avg(wday, chunk_nb, l1, _hname, _sdesc, _metric)




def compute_memory_smooth():
    global _raw_t, datas, _t
    for (wday, day) in datas.iteritems():
        #_t = []
        last_good = -1
        cur_l = None
        for d in day:
            if not d:
                _t.append(last_good)
                continue
            last_good = d.get_load()
            if not cur_l:
                cur_l = Load(m=1, initial_value=last_good)
            cur_l.update_load(last_good, 5)
            #_t.append(last_good)
            _t.append(cur_l.get_load())#last_good)


        #ultra_raw = []
    
        # Also get the raw one
        raw_day = raw_datas[wday]
        #_raw_t = []
        cur_l = None
        i = -1
        for d in raw_day:
            i += 1
            if not d:
                debug("No entry for", wday, i)
                _raw_t.append(last_good)
                ultra_raw.append(last_good)
                continue
            last_good = d
            if not cur_l:
                cur_l = Load(m=1, initial_value=last_good)
            cur_l.update_load(last_good, 10)
            #_raw_t.append(last_good)
            _raw_t.append(cur_l.get_load())#last_good)
            ultra_raw.append(last_good)
        
        #print _t

        avg_t = sum(_t)/len(_t)
        avg_raw_t = sum(_raw_t)/len(_t)

        pct_failed = 0.0
        for i in xrange(len(_raw_t)):
            try:
                pct_failed += abs(_raw_t[i] - _t[i]) / _t[i]
            except ZeroDivisionError:
                pass
        #print "pct_failed", pct_failed
        pct_failed /= len(_raw_t)
        #print "pct_failed", pct_failed




def get_graph_values(hname, sdesc, metric, mkey):
    _from_mongo = []
    for wday in range(0, 7):
        for chunk_nb in range(nb_chunks):            
            key = get_key(hname, sdesc, metric, wday, chunk_nb)#hname+sdesc+metric+'week'+str(wday)+'Vtrend'+str(chunk_nb)
            doc = coll.find_one({'_id':key})
            if doc:
                # WAS 
                _from_mongo.append(doc[mkey])
            else:
                debug("Warning : no db entry for", key)
                prev_wday, prev_chunk_nb = get_previous_chunk(wday, chunk_nb)
                key = get_key(hname, sdesc, metric, prev_wday, prev_chunk_nb)#hname+sdesc+metric+'week'+str(prev_wday)+'Vtrend'+str(prev_chunk_nb)
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
                      help='CSV to import')
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
    
    opts, args = parser.parse_args()

    
    do_debug = opts.do_debug
        
    
    # ok open the connexion
    open_connexion()
    

    hname = opts.host_name
    sdesc = opts.service_description
    metric = opts.metric
    do_print = opts.do_print
    csv_file = opts.csv_file

    if do_print and plt is None:
        print "ERROR : cannot import matplotlib, please install it"
        sys.exit(2)
        

    if csv_file:
        reader = open_csv(csv_file)
        import_csv(reader, hname, sdesc, metric)
        compute_memory_smooth()

    if do_print:    
        _from_mongo = get_graph_values(hname, sdesc, metric, 'VtrendSmooth')
        _from_mongo_short = get_graph_values(hname, sdesc, metric, 'VcurrentSmooth')
        _el_raw = get_graph_values(hname, sdesc, metric, 'Vcurrent')
        #print "PYMONGO?", _from_mongo
        pct_failed = 0.0
        for i in xrange(len(_from_mongo)):
            try:
                #pct_failed += abs(_raw_t[i] - _from_mongo[i]) / _from_mongo[i]
                pct_failed += abs(_from_mongo_short[i] - _from_mongo[i]) / _from_mongo[i]
            except ZeroDivisionError:
                pass
            except IndexError:
                print "Was trying to get", i
            except TypeError:
                print "Was trying to get", i
        pct_failed /= len(_from_mongo)
        debug("pct_failed MONGO:", pct_failed)

        if csv_file:
            plt.plot(_times, _t, 'b', _times, ultra_raw, 'c', _times, _from_mongo, 'r', _times, _from_mongo_short, 'm')#, _times, _el_raw, 'y')
            plt.axis(ymin=0)
            plt.show()
        else:
            plt.plot(_times, _from_mongo, 'r', _times, _from_mongo_short, 'y')
            plt.show()
            
