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

# TODO : Also buffering raw data, not only cPickle
# TODO : Better buffering like FIFO Buffer

import re
from socket import socket
import cPickle
import struct

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'graphite_perfdata',
    'external': False,
    }


# Called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info("[Graphite broker] Get a graphite data module for plugin %s" % mod_conf.get_name())
    instance = Graphite_broker(mod_conf)
    return instance


# Class for the Graphite Broker
# Get broks and send them to a Carbon instance of Graphite
class Graphite_broker(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.host = getattr(modconf, 'host', 'localhost')
        self.port = int(getattr(modconf, 'port', '2003'))
        self.use_pickle = getattr(modconf, 'use_pickle', '0') == '1'
        if self.use_pickle:
            self.port = int(getattr(modconf, 'port', '2004'))
        else:
            self.port = int(getattr(modconf, 'port', '2003'))
        self.tick_limit = int(getattr(modconf, 'tick_limit', '300'))
        self.buffer = []
        self.ticks = 0
        self.host_dict = {}
        self.svc_dict = {}
        self.multival = re.compile(r'_(\d+)$')

        # optional "sub-folder" in graphite to hold the data of a specific host
        self.graphite_data_source = self.illegal_char.sub('_',
                                   getattr(modconf, 'graphite_data_source', ''))


    # Called by Broker so we can do init stuff
    # TODO: add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        logger.info("[Graphite broker] I init the %s server connection to %s:%d" % (self.get_name(), str(self.host), self.port))
        try:
            self.con = socket()
            self.con.connect((self.host, self.port))
        except IOError, err:
                logger.error("[Graphite broker] Graphite Carbon instance network socket! IOError:%s" % str(err))
                raise
        logger.info("[Graphite broker] Connection successful to  %s:%d" % (str(self.host), self.port))

    # Sending data to Carbon. In case of failure, try to reconnect and send again. If carbon instance is down
    # Data are buffered.
    def send_packet(self, p):
        try:
            self.con.sendall(p)
        except IOError, err:
            logger.error("[Graphite broker] Failed sending data to the Graphite Carbon instance ! Trying to reconnect ... ")
            try:
                self.init()
                self.con.sendall(p)
            except IOError:
                raise

    # For a perf_data like /=30MB;4899;4568;1234;0  /var=50MB;4899;4568;1234;0 /toto=
    # return ('/', '30'), ('/var', '50')
    def get_metric_and_value(self, perf_data):
        res = []
        s = perf_data.strip()
        # Get all metrics non void
        elts = s.split(' ')
        metrics = [e for e in elts if e != '']

        for e in metrics:
            logger.debug("[Graphite broker] Groking: %s" % str(e))
            elts = e.split('=', 1)
            if len(elts) != 2:
                continue

            name = self.illegal_char.sub('_', elts[0])
            name = self.multival.sub(r'.\1', name)

            raw = elts[1]
            # get metric value and its thresholds values if they exist
            if ';' in raw and len(filter(None, raw.split(';'))) >= 3:
                elts = raw.split(';')
                name_value = {name: elts[0], name + '_warn': elts[1], name + '_crit': elts[2]}
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
            logger.debug("[Graphite broker] End of grok: %s, %s" % (name, str(value)))
            for key, value in name_value.items():
                res.append((key, value))
        return res


    # Prepare service custom vars
    def manage_initial_service_status_brok(self, b):
        if '_GRAPHITE_POST' in b.data['customs']:
            self.svc_dict[(b.data['host_name'], b.data['service_description'])] = b.data['customs']


    # Prepare host custom vars
    def manage_initial_host_status_brok(self, b):
        if '_GRAPHITE_PRE' in b.data['customs']:
            self.host_dict[b.data['host_name']] = b.data['customs']


    # A service check result brok has just arrived, we UPDATE data info with this
    def manage_service_check_result_brok(self, b):
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

        desc = self.illegal_char.sub('_', data['service_description'])
        if (data['host_name'], data['service_description']) in self.svc_dict:
            customs_datas = self.svc_dict[(data['host_name'], data['service_description'])]
            if '_GRAPHITE_POST' in customs_datas:
                desc = ".".join((desc, customs_datas['_GRAPHITE_POST']))

        check_time = int(data['last_chk'])

        logger.debug("[Graphite broker] Hostname: %s, Desc: %s, check time: %d, perfdata: %s" % (hname, desc, check_time, str(perf_data)))

        if self.graphite_data_source:
            path = '.'.join((hname, self.graphite_data_source, desc))
        else:
            path = '.'.join((hname, desc))

        if self.use_pickle:
            # Buffer the performance data lines
            for (metric, value) in couples:
                if value:
                    self.buffer.append(("%s.%s" % (path, metric),
                                       ("%d" % check_time,
                                        "%s" % value)))

        else:
            lines = []
            # Send a bulk of all metrics at once
            for (metric, value) in couples:
                if value:
                    lines.append("%s.%s %s %d" % (path, metric,
                                                  value, check_time))
            packet = '\n'.join(lines) + '\n'  # Be sure we put \n every where
            logger.debug("[Graphite broker] Launching: %s" % packet)
            try:
                self.send_packet(packet)
            except IOError, err:
                logger.error("[Graphite broker] Failed sending to the Graphite Carbon. Data are lost")


    # A host check result brok has just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
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
            try:
                self.send_packet(packet)
            except IOError, err:
                logger.error("[Graphite broker] Failed sending to the Graphite Carbon. Data are lost")
             

    def hook_tick(self, brok):
        """Each second the broker calls the hook_tick function
           Every tick try to flush the buffer
        """
        if self.use_pickle:
            if self.ticks >= self.tick_limit:
                # If the number of ticks where data was not
                # sent successfully to Graphite reaches the bufferlimit.
                # Reset the buffer and reset the ticks
                logger.error("[Graphite broker] Buffering time exceeded. Freeing buffer")
                self.buffer = []
                self.ticks = 0
                return
           
            # Format the data
            payload = cPickle.dumps(self.buffer)
            header = struct.pack("!L", len(payload))
            packet = header + payload

            try:
	        self.send_packet(packet)
                # Flush the buffer after a successful send to Graphite
                self.buffer = []
                self.ticks = 0
            except IOError, err:
                self.ticks += 1
                logger.error("[Graphite broker] Sending data Failed. Buffering state : %s / %s" % ( self.ticks , self.tick_limit ))
            

