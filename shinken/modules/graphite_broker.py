#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


"""This Class is a plugin for the Shinken Broker. It is in charge
to brok information of the service/host perfdatas into the Graphite
backend. http://graphite.wikidot.com/start
"""

import re
from socket import socket

from shinken.basemodule import BaseModule

properties = {
    'daemons' : ['broker'],
    'type' : 'graphite_perfdata',
    'external' : False,
    }


#called by the plugin manager to get a broker
def get_instance(mod_conf):
    print "Get a graphite data module for plugin %s" % mod_conf.get_name()
    instance = Graphite_broker(mod_conf)
    return instance



#Class for the Merlindb Broker
#Get broks and puts them in merlin database
class Graphite_broker(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.host = getattr(modconf, 'host', 'localhost')
        self.port = int(getattr(modconf, 'port', '2003'))


    #Called by Broker so we can do init stuff
    #TODO : add conf param to get pass with init
    #Conf from arbiter!
    def init(self):
        print "[%s] I init the graphite server connection to %s:%s" % (self.get_name(), self.host, self.port) 
        self.con = socket()
        self.con.connect( (self.host, self.port))


    # For a perf_data like /=30MB;4899;4568;1234;0  /var=50MB;4899;4568;1234;0 /toto=
    # return ('/', '30'), ('/var', '50')
    def get_metric_and_value(self, perf_data):
        res = []
        s = perf_data.strip()
        # Get all metrics non void
        elts = s.split(' ')
        metrics = [e for e in elts if e != '']

        for e in metrics:
 #           print "Graphite : groking : ", e
            elts = e.split('=', 1)
            if len(elts) != 2:
                continue
            name = elts[0]
            raw = elts[1]
            # get the first value of ;
            if ';' in raw:
                elts = raw.split(';')
                value = elts[0]
            else:
                value = raw
            # bailout if need
            if value == '':
                continue

            # Try to get the int/float in it :)
            m = re.search("(\d*\.*\d*)", value)
            if m:
                value = m.groups(0)[0]
            else:
                continue
#            print "graphite : got in the end :", name, value
            res.append((name, value))
        return res


    # A service check have just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
        data = b.data
        
        perf_data = data['perf_data']
        hname = data['host_name']
        desc = data['service_description']
        check_time = int(data['last_chk'])

#        print "Graphite:", hname, desc, check_time, perf_data
        
        couples = self.get_metric_and_value(perf_data)

        # If no values, we can exit now
        if len(couples) == 0:
            return

        lines = []
        # Send a bulk of all metrics at once
        for (metric, value) in couples:
            lines.append("%s.%s.%s %s %d" % (hname, desc, metric, value, check_time))
        packet = '\n'.join(lines) + '\n' # Be sure we put \n every where
#        print "Graphite launching :", packet
        self.con.sendall(packet)



    # An host check have just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
        data = b.data
        
        perf_data = data['perf_data']
        hname = data['host_name']
        check_time = int(data['last_chk'])

 #       print "Graphite:", hname, check_time, perf_data
        
        couples = self.get_metric_and_value(perf_data)

        # If no values, we can exit now
        if len(couples) == 0:
            return

        lines = []
        # Send a bulk of all metrics at once
        for (metric, value) in couples:
            lines.append("%s.__HOST__.%s %s %d" % (hname, metric, value, check_time))
        packet = '\n'.join(lines) + '\n' # Be sure we put \n every where
  #      print "Graphite launching :", packet
        self.con.sendall(packet)
