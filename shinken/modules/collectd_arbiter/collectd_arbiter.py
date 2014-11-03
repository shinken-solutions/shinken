#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Thibault Cohen, thibault.cohen@savoirfairelinux.com
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

"""
Collectd Plugin for Receiver or arbiter
"""

import os
import re
import threading
import dummy_threading
import time
import traceback
from itertools import izip
from collections import namedtuple

#############################################################################

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand #, ManyExternalCommand
from shinken.log import logger

#############################################################################

from .collectd_parser import (
    CollectdException,
    DS_TYPE_COUNTER, DS_TYPE_GAUGE, DS_TYPE_DERIVE, DS_TYPE_ABSOLUTE,
    DEFAULT_PORT, DEFAULT_IPv4_GROUP
)
from .collectd_shinken_parser import (
    Data, Values, Notification,
    ShinkenCollectdReader
)

#############################################################################

properties = {
    'daemons': ['arbiter', 'receiver'],
    'type': 'collectd',
    'external': True,
    }


#############################################################################

def get_instance(plugin):
    """ This function is called by the module manager
    to get an instance of this module
    """
    if hasattr(plugin, "multicast"):
        multicast = plugin.multicast.lower() in ("yes", "true", "1")
    else:
        multicast = False

    if hasattr(plugin, 'host'):
        host = plugin.host
    else:
        host = DEFAULT_IPv4_GROUP
        multicast = True

    if hasattr(plugin, 'port'):
        port = int(plugin.port)
    else:
        port = DEFAULT_PORT

    if hasattr(plugin, 'grouped_collectd_plugins'):
        grouped_collectd_plugins = [name.strip()
                                    for name in plugin.grouped_collectd_plugins.split(',')]
    else:
        grouped_collectd_plugins = []

    logger.info("[Collectd] Using host=%s port=%d multicast=%d" % (host, port, multicast))

    instance = Collectd_arbiter(plugin, host, port, multicast, grouped_collectd_plugins)
    return instance

#############################################################################

MP = MetricPoint = namedtuple('MetricPoint',
                         'dstype rawval val time here_time')


class Element(object):
    """ Element store service name and all perfdatas before send it in a external command """

    def __init__(self, host_name, sdesc, interval, last_sent=None):
        self.host_name = host_name
        self.sdesc = sdesc
        self.perf_datas = {}
        self.interval = interval
        if not last_sent:
            last_sent = time.time()
        # for the first time we'll wait 2*interval to be sure to get a complete data set :
        self.last_sent = last_sent + 2*interval

    def _last_update(self, _op=max):
        ''' Return the maximal time of last reported perf data.
        If _op is different then returns that.
        :param _op: min or max
        :return:
        '''
        return _op(met_pts[-1].here_time
                   for met_pts in self.perf_datas.values())

    @property
    def last_full_update(self):
        ''' :return: The last "full" update time of this element. i.e. the metric mininum last update own time. '''
        return self._last_update(min)

    @property
    def send_ready(self):
        '''
        :return: True if this element is ready to have its perfdata sent. False otherwise.
        '''
        return ( self.perf_datas
        #         and self.last_full_update > self.last_sent   # -> send_ready if ALL perfdata were updated (> last_sent).
                 and self._last_update() > self.last_sent      # -> send_ready if AT LEAST ONE perfdata was updated
                 and time.time() > self.last_sent + self.interval)

    def __str__(self):
        return '%s.%s' % (self.host_name, self.sdesc)

    def add_perf_data(self, mname, mvalues, mtime):
        """ Add perf datas to this element.
        :param mname:   The metric name.
        :param mvalues: The metric read values.
        :param mtime:   The "epoch" time when the values were read.
        """
        if not mvalues:
            return

        res = []
        now = time.time()

        oldvalues = self.perf_datas.get(mname, None)
        if oldvalues is None:
            logger.info('%s : New perfdata: %s : %s' % (self, mname, mvalues))
            for (dstype, val) in mvalues:
                # we also retain the local time (`now´) more for convenience purpose.
                res.append(MP(dstype, val, val, mtime, now))
        else:
            for met_point, (dstype, val) in izip(oldvalues, mvalues):
                difftime = mtime - met_point.time
                if difftime < 1:
                    continue
                if dstype in (DS_TYPE_COUNTER, DS_TYPE_DERIVE, DS_TYPE_ABSOLUTE):
                    res.append(MP(dstype, val, (val - met_point.rawval) / float(difftime), mtime, now))
                elif dstype == DS_TYPE_GAUGE:
                    res.append(MP(dstype, val, val, mtime, now))

        if res:
           self.perf_datas[mname] = res


    def get_command(self):
        """ Look if this element has data to be sent to Shinken.
        :return
            - None if element has not all its perf data refreshed since last sent..
            - The command to be sent otherwise.
        """
        if not self.send_ready:
            return

        res = ''
        max_time = None
        for met_name, values_list in sorted(self.perf_datas.items(), key=lambda i: i[0]):
            for met_idx, met_pt in enumerate(values_list):
                value_to_str = lambda v: '%f' % v if isinstance(met_pt.val, float) else str
                met_value = value_to_str(met_pt.val)
                res += ('{met_name}%s={met_value} ' % (
                    '_{met_idx}' if len(values_list) > 1 else ''
                    )).format(**locals())
                if max_time is None or met_pt.here_time > max_time:
                    max_time = met_pt.here_time

        self.last_sent = time.time()
        return '[%d] PROCESS_SERVICE_OUTPUT;%s;%s;CollectD|%s' % (
                int(max_time), self.host_name, self.sdesc, res)

#############################################################################

class Collectd_arbiter(BaseModule):
    """ Main class for this collecitd module """

    def __init__(self, modconf, host, port, multicast, grouped_collectd_plugins=None, use_dedicated_thread=False):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port
        self.multicast = multicast
        if grouped_collectd_plugins is None:
            grouped_collectd_plugins = []
        self.elements = {}
        self.grouped_collectd_plugins = grouped_collectd_plugins

        self.use_dedicated_thread = use_dedicated_thread
        th_mgr = ( threading if use_dedicated_thread
                   else dummy_threading )
        self.lock = th_mgr.Lock() # protect the access to self.elements
        self.send_ready = False


    def _read_collectd_packet(self, reader):
        ''' Read and interpret a packet from collectd.
        :param reader: A collectd Reader instance.
        '''
        elements = self.elements
        lock = self.lock

        send_ready = False
        item_iterator = reader.interpret()
        while True:
            try:
                item = next(item_iterator)
            except StopIteration:
                break
            except CollectdException as err:
                logger.error('CollectdException: %s' % err)
                continue

            assert isinstance(item, Data)
            #logger.info("[Collectd] < %s" % item)

            if isinstance(item, Notification):
                cmd = item.get_message_command()
                if cmd is not None:
                    #logger.info('-> %s', cmd)
                    self.from_q.put(ExternalCommand(cmd))

            elif isinstance(item, Values):
                name = item.get_name()
                elem = elements.get(name, None)
                if elem is None:
                    elem = Element(item.host,
                                   item.get_srv_desc(),
                                   item.interval)
                    logger.info('Created %s ; interval=%s' % (elem, elem.interval))
                else:
                    # sanity check:
                    # make sure element interval is updated when it's changed on collectd client:
                    if elem.interval != item.interval:
                        logger.info('%s : interval changed from %s to %s ; adapting..' % (
                                    name, elem.interval, item.interval))
                        with lock:
                            elem.interval = item.interval
                            # also reset last_update time so that we'll wait that before resending its data:
                            elem.last_sent = time.time() + item.interval
                            elem.perf_datas.clear() # should we or not ?

                # now we can add this perf data:
                with lock:
                    elem.add_perf_data(item.get_metric_name(), item, item.time)
                    if name not in elements:
                        elements[name] = elem
                if elem.send_ready:
                    send_ready = True
        #end for


    def _read_collectd(self, reader):
        while not self.interrupted:
            self._read_collectd_packet(reader)


    # When you are in "external" mode, that is the main loop of your process
    def do_loop_turn(self):

        use_dedicated_thread = self.use_dedicated_thread
        elements = self.elements
        lock = self.lock
        now = time.time()
        clean_every = 15
        report_every = 60
        next_clean = now + clean_every
        next_report = now + report_every
        n_cmd_sent = 0

        reader = ShinkenCollectdReader(self.host, self.port, self.multicast,
                                       grouped_collectd_plugins=self.grouped_collectd_plugins)
        try:
            if use_dedicated_thread:
                collectd_reader_thread = threading.Thread(target=self._read_collectd, args=(reader,))
                collectd_reader_thread.start()

            while not self.interrupted:

                if use_dedicated_thread:
                    time.sleep(1)
                else:
                    self._read_collectd_packet(reader)

                tosend = []
                with lock:
                    for elem in elements.itervalues():
                        cmd = elem.get_command()
                        if cmd:
                            tosend.append(cmd)
                # we could send those in one shot !
                # if it existed an ExternalCommand*s* items class.. TODO.
                for cmd in tosend:
                    self.from_q.put(ExternalCommand(cmd))
                n_cmd_sent += len(tosend)

                now = time.time()
                if now > next_clean:
                    next_clean = now + clean_every
                    if use_dedicated_thread:
                        if not collectd_reader_thread.isAlive() and not self.interrupted:
                            raise Exception('Collectd read thread unexpectedly died.. exiting.')

                    todel = []
                    with lock:
                        for name, elem in elements.iteritems():
                            for perf_name, met_values in elem.perf_datas.items():
                                if met_values[0].here_time < now - 3*elem.interval:
                                    # this perf data has not been updated for more than 3 intervals,
                                    # purge it.
                                    del elem.perf_datas[perf_name]
                                    logger.info('%s %s: 3*interval without data, purged.' % (elem, perf_name))
                            if not elem.perf_datas:
                                todel.append(name)
                        for name in todel:
                            logger.info('%s : not anymore updated > purged.' % name)
                            del elements[name]

                if now > next_report:
                    next_report = now + report_every
                    logger.info('%s commands reported during last %s seconds.' % (n_cmd_sent, report_every))
                    n_cmd_sent = 0

        except Exception as err:
            logger.error("[Collectd] Unexpected error: %s ; %s" % (err, traceback.format_exc()))
            raise
        finally:
            reader.close()
            if use_dedicated_thread:
                collectd_reader_thread.join()
