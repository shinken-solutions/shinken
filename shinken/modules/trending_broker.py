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

"""This Class is a plugin for the Shinken Broker. It is in charge
to brok information of the service/host perfdatas into the Graphite
backend. http://graphite.wikidot.com/start
"""

import re
import math

from shinken.basemodule import BaseModule
from shinken.util import get_sec_from_morning, get_wday
from shinken.log import logger
from shinken.load import Load

try:
    from pymongo.connection import Connection
except ImportError:
    Connection = None

try:
    from pymongo import ReplicaSetConnection, ReadPreference
except ImportError:
    ReplicaSetConnection = None
    ReadPreference = None


properties = {
    'daemons': ['broker'],
    'type': 'trending_broker',
    'external': False,
    }


# Called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info("[Trengind broker] Get a trending data module for plugin %s" % mod_conf.get_name())
    instance = Trending_broker(mod_conf)
    return instance


# Class for the Trending Broker
# Get broks and send them to a Mongodb instance with smooth averages
class Trending_broker(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.backend = getattr(modconf, 'backend', 'mongodb')
        self.uri = getattr(modconf, 'uri', 'localhost')
        self.database = getattr(modconf, 'database', 'shinken')
        self.replica_set = getattr(modconf, 'replica_set', '')

        # 15min chunks
        self.chunk_interval = int(getattr(modconf, 'chunk_interval', '900'))
        self.nb_chunks = int(math.ceil(86400.0/self.chunk_interval))

        # Some used varaible init
        self.con = None
        self.db = None
        self.col = None

        self.host_dict = {}
        self.svc_dict = {}
        

    # Called by Broker so we can do init stuff
    # TODO: add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        logger.info("[Trending broker] I init the %s server connection to %s:%s (%s)" % (self.get_name(), self.backend, self.uri, self.replica_set))
        if self.replica_set:
            self.con = ReplicaSetConnection(self.uri, replicaSet=self.replica_set, safe=True)
        else:
            # Old versions of pymongo do not known about fsync
            if ReplicaSetConnection:
                self.con = Connection(self.uri, safe=True)
            else:
                self.con = Connection(self.uri, safe=True)

        # Open a connection
        self.db = getattr(self.con, self.database)
        self.col = self.db['trending']


    # For a perf_data like /=30MB;4899;4568;1234;0  /var=50MB;4899;4568;1234;0 /toto=
    # return ('/', '30'), ('/var', '50')
    def get_metric_and_value(self, perf_data):
        res = []
        s = perf_data.strip()
        # Get all metrics non void
        elts = s.split(' ')
        metrics = [e for e in elts if e != '']

        for e in metrics:
            logger.debug("[Trending broker] Groking: %s" % str(e))
            elts = e.split('=', 1)
            if len(elts) != 2:
                continue
            name = self.illegal_char.sub('_', elts[0])

            raw = elts[1]
            # get metric value and its thresholds values if they exist
            if ';' in raw and len(filter(None, raw.split(';'))) >= 3:
                elts = raw.split(';')
                name_value = {name: elts[0]}#, name + '_warn': elts[1], name + '_crit': elts[2]}
            # get the first value of ;
            else:
                value = raw
                name_value = {name: raw}
            # bailout if need
            if name_value[name] == '':
                continue

            # Try to get the int/float in it :)
            for key, value in name_value.items():
                m = re.search("(-?\d*\.?\d*)(.*)", value)
                if m:
                    name_value[key] = m.groups(0)[0]
                else:
                    continue
            logger.debug("[Trending broker] End of grok: %s, %s" % (name, str(value)))
            for key, value in name_value.items():
                res.append((key, value))
        return res


    # Ok a quick and dirty load computation
    def quick_update(self, prev_val, new_val, m, interval):
        l = Load(m=m, initial_value=prev_val)
        l.update_load(new_val, interval)
        return l.get_load()


    def get_previous_chunk(self, wday, chunk_nb):
        if chunk_nb == 0:
            chunk_nb = nb_chunks - 1
            wday -= 1
        else:
            chunk_nb -= 1
        wday = wday % 7
        return (wday, chunk_nb)

    def get_key(self, hname, sdesc, metric, wday, chunk_nb):
        return hname+'.'+sdesc+'.'+metric+'.'+'week'+'.'+str(wday)+'.'+'Vtrend'+'.'+str(chunk_nb)


    def update_avg(self, wday, chunk_nb, l1, hname, sdesc, metric):
        coll = self.col
        key = self.get_key(hname, sdesc, metric, wday, chunk_nb)#hname+sdesc+metric+'week'+str(wday)+'Vtrend'+str(chunk_nb)
        doc = coll.find_one({'_id' : key})
        if not doc:
            doc = {'hname':hname, 'sdesc':sdesc, 'metric':metric, 'cycle':'week',
                   'wday':wday, 'chunk_nb':chunk_nb, 'Vtrend':l1, '_id':key,
                   'VtrendSmooth':l1, 'VcurrentSmooth':l1, 'Vcurrent':l1
                   }
            coll.save(doc)
        else:
            prev_val = doc['Vtrend']
        
            new_Vtrend = self.quick_update(prev_val, l1, 5, 5)
        
            # Now we smooth with the last value
            # And by default, we are using the current value
            new_VtrendSmooth = doc['VtrendSmooth']

            prev_doc = None
            cur_wday = wday
            cur_chunk_nb = chunk_nb
            # Ok by default take the current avg
            prev_val = doc['VtrendSmooth']
            prev_val_short = doc['VcurrentSmooth']
        
            cur_wday, cur_chunk_nb = self.get_previous_chunk(cur_wday, cur_chunk_nb)
            prev_key = self.get_key(hname, sdesc, metric, cur_wday, cur_chunk_nb)#hname+sdesc+metric+'week'+str(cur_wday)+'Vtrend'+str(cur_chunk_nb)
            prev_doc = coll.find_one({'_id' : prev_key})
            if prev_doc:
                prev_val = prev_doc['VtrendSmooth']
                prev_val_short = prev_doc['VcurrentSmooth']
            else:
                print "OUPS, the key", key, "do not have a previous entry", cur_wday, cur_chunk_nb

            # Ok really update the value now
            print "WFT?", prev_val, new_Vtrend, type(prev_val), type(new_Vtrend)
            
            new_VtrendSmooth = self.quick_update(prev_val, new_Vtrend, 1, 5)

            # Ok and now last minutes trending
            new_VcurrentSmooth = self.quick_update(prev_val_short, l1, 1, 15)
            d = (abs(new_VcurrentSmooth - new_VtrendSmooth)/float(new_VtrendSmooth)) * 100
        
            coll.update({'_id' : key}, {'$set' : { 'Vtrend': new_Vtrend, 'VtrendSmooth': new_VtrendSmooth, 'VcurrentSmooth' : new_VcurrentSmooth, 'Vcurrent':l1  }})



    # Prepare service custom vars
    def manage_initial_service_status_brok(self, b):
        policies = b.data['trending_policies']
        if policies:
            self.svc_dict[(b.data['host_name'], b.data['service_description'])] = policies
        

    # Prepare host custom vars
    def manage_initial_host_status_brok(self, b):
        policies = b.data['trending_policies']
        if policies:
            self.host_dict[b.data['host_name']] = policies


    # A service check result brok has just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data

        # Maybe this service is just unknown and without policies, if so, bail out
        policies = self.svc_dict.get((data['host_name'], data['service_description']), [])
        if not policies:
            return

        # Ok there are some real policies
        print "OK POLICIES FOR", (data['host_name'], data['service_description']), policies
        
        perf_data = data['perf_data']
        couples = self.get_metric_and_value(perf_data)

        # If no values, we can exit now
        if len(couples) == 0:
            return

        
        hname = data['host_name']#self.illegal_char.sub('_', data['host_name'])
        #if data['host_name'] in self.host_dict:
        #    customs_datas = self.host_dict[data['host_name']]
        #    if '_GRAPHITE_PRE' in customs_datas:
        #        hname = ".".join((customs_datas['_GRAPHITE_PRE'], hname))

        sdesc = data['service_description']#self.illegal_char.sub('_', data['service_description'])
        #if (data['host_name'], data['service_description']) in self.svc_dict:
        #    customs_datas = self.svc_dict[(data['host_name'], data['service_description'])]
        #    if '_GRAPHITE_POST' in customs_datas:
        #        desc = ".".join((desc, customs_datas['_GRAPHITE_POST']))

        check_time = int(data['last_chk'])

        logger.debug("[Trending broker] Hostname: %s, Desc: %s, check time: %d, perfdata: %s, policies: %s" % (hname, sdesc, check_time, str(perf_data), policies))

        # Ok now the real stuff is here
        for p in policies:
            for (metric, value) in couples:
                try:
                    value = float(value)
                except ValueError:
                    return
                if value is not None: 
                    print "DUMPING", (metric, value), "for", p

                    sec_from_morning = get_sec_from_morning(check_time)
                    wday = get_wday(check_time)
                    
                    chunk_nb = sec_from_morning / self.chunk_interval
                    
                    # Now update mongodb
                    print "UPDATING DB", wday, chunk_nb, value, hname, sdesc, metric, type(value)
                    self.update_avg(wday, chunk_nb, value, hname, sdesc, metric)
                    
                    

    # A host check result brok has just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
        return
        
        data = b.data

        perf_data = data['perf_data']
        couples = self.get_metric_and_value(perf_data)

        # If no values, we can exit now
        if len(couples) == 0:
            return

        hname = self.illegal_char.sub('_', data['host_name'])
        if data['host_name'] in self.host_dict:
            customs_datas = self.host_dict[data['host_name']]
            if '_GRAPHITE_PRE' in customs_datas:
                hname = ".".join((customs_datas['_GRAPHITE_PRE'], hname))

        check_time = int(data['last_chk'])

        logger.debug("[Graphite broker] Hostname %s, check time: %d, perfdata: %s" % (hname, check_time, str(perf_data)))

        if self.graphite_data_source:
            path = '.'.join((hname, self.graphite_data_source))
        else:
            path = hname

        if self.use_pickle:
            # Buffer the performance data lines
            for (metric, value) in couples:
                if value:
                    self.buffer.append(("%s.__HOST__.%s" % (path, metric),
                                       ("%d" % check_time,
                                        "%s" % value)))
        else:
            lines = []
            # Send a bulk of all metrics at once
            for (metric, value) in couples:
                if value:
                    lines.append("%s.__HOST__.%s %s %d" % (path, metric,
                                                           value, check_time))
            packet = '\n'.join(lines) + '\n'  # Be sure we put \n every where
            logger.debug("[Graphite broker] Launching: %s" % packet)
            self.con.sendall(packet)


