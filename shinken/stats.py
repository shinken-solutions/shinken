#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

import threading
import time
import json
import hashlib
import base64
import socket
import traceback

from shinken.log import logger

# For old users python-crypto was not mandatory, don't break their setup
try:
    from Crypto.Cipher import AES
except ImportError:
    logger.debug('Cannot find python lib crypto: export to kernel.shinken.io isnot available')
    AES = None

from shinken.http_client import HTTPClient, HTTPException


BLOCK_SIZE = 16


def pad(data):
    pad = BLOCK_SIZE - len(data) % BLOCK_SIZE
    return data + pad * chr(pad)


def unpad(padded):
    pad = ord(padded[-1])
    return padded[:-pad]



class Stats(object):
    def __init__(self):
        self.name = ''
        self.type = ''
        self.app = None
        self.stats = {}
        # There are two modes that are not exclusive
        # first the kernel mode
        self.api_key = ''
        self.secret = ''
        self.http_proxy = ''
        self.con = HTTPClient(uri='http://kernel.shinken.io')
        # then the statsd one
        self.statsd_interval = 5
        self.statsd_types = ['system', 'queue', 'perf']
        self.statsd_sock = None
        self.statsd_addr = None
        self.statsd_types = 'system,object,queue,perf'
        self.statsd_pattern = None
        self.name_cache = {}


    def launch_reaper_thread(self):
        self.reaper_thread = threading.Thread(None, target=self.reaper,
                                              name='stats-reaper')
        self.reaper_thread.daemon = True
        self.reaper_thread.start()


    def launch_harvester_thread(self):
        self.harvester_thread = threading.Thread(None, target=self.harvester,
                                                 name='stats-harvester')
        self.harvester_thread.daemon = True
        self.harvester_thread.start()

    def register(self, app, name, _type, api_key='', secret='', http_proxy='',
                 statsd_host='localhost', statsd_port=8125, statsd_prefix='shinken',
                 statsd_enabled=False, statsd_interval=5, statsd_types=None,
                 statsd_pattern=None):
        self.app = app
        self.name = name
        self.type = _type
        # kernel.io part
        self.api_key = api_key
        self.secret = secret
        self.http_proxy = http_proxy
        # local statsd part
        self.statsd_host = statsd_host
        self.statsd_port = statsd_port
        self.statsd_prefix = statsd_prefix
        self.statsd_enabled = statsd_enabled
        self.statsd_interval = statsd_interval
        if statsd_types is not None:
            self.statsd_types = [t.strip() for t in statsd_types.split(",") if t.strip()]
        if statsd_pattern is not None:
            self.statsd_pattern = statsd_pattern
        self.name_cache = {}

        if self.statsd_enabled:
            logger.debug('Loading statsd communication with %s:%s.%s',
                         self.statsd_host, self.statsd_port, self.statsd_prefix)
            self.load_statsd()

        # Also load the proxy if need
        self.con.set_proxy(self.http_proxy)


    # Tells whether statsd is enabled and stats should be sent
    def is_statsd_enabled(self):
        return (self.statsd_sock is not None and
                self.name and
                self.app is not None)


    # Tells whether kernel.status.io exporter is enabled
    def is_shinkenio_enabled(self):
        return (self.name and self.api_key and self.secret)


    # Let be crystal clear about why I don't use the statsd lib in python: it's crappy.
    # how guys did you fuck this up to this point? django by default for the conf?? really?...
    # So raw socket are far better here
    def load_statsd(self):
        try:
            self.statsd_addr = (socket.gethostbyname(self.statsd_host), self.statsd_port)
            self.statsd_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        except (socket.error, socket.gaierror), exp:
            logger.error('Cannot create statsd socket: %s' % exp)
            return


    # Calculates a complete metric name from prefix or pattern
    # Pattern has precedence on prefix if defined
    # As formatting may involve extra CPU, we cache the calculated metric
    # name to speed next calls.
    def get_metric_name(self, name):
        if name not in self.name_cache:
            if self.statsd_pattern is not None:
                try:
                    self.name_cache[name] = self.statsd_pattern.format(
                        metric=name,
                        name=self.name,
                        service=self.type)
                except Exception, e:
                    logger.error("Failed to build metric name, check your "
                                 "statsd_pattern parameter: %s" % e)
            elif self.prefix:
                self.name_cache[name] = "%s.%s" % (self.statsd_prefix, name)
            else:
                self.name_cache[name] = name
        return self.name_cache[name]


    # Sends a metric to statsd daemon
    def send_metric(self, packet):
        try:
            self.statsd_sock.sendto(packet, self.statsd_addr)
        except (socket.error, socket.gaierror):
            # cannot send? ok not a huge problem here and cannot
            # log because it will be far too verbose :p
            self.load_statsd()


    # Updates internal stats for sending to kernel.shinken.io
    def update_internal_stats(self, k, v):
        _min, _max, nb, _sum = self.stats.get(k, (None, None, 0, 0))
        nb += 1
        _sum += v
        if _min is None or v < _min:
            _min = v
        if _max is None or v > _max:
            _max = v
        self.stats[k] = (_min, _max, nb, _sum)


    # Will increment a counter key
    def incr(self, k, v, t):
        if self.statsd_sock and self.name and t in self.statsd_types:
            name = self.get_metric_name(k)
            self.update_internal_stats(k, v)
            packet = '%s:%d|c' % (name, v)
            self.send_metric(packet)


    # Will send a gauge value
    def gauge(self, k, v, t):
        if self.statsd_sock and self.name and t in self.statsd_types:
            name = self.get_metric_name(k)
            self.update_internal_stats(k, v)
            packet = '%s:%d|g' % (name, v)
            self.send_metric(packet)


    # Will increment a timer key, if None, start at 0
    def timing(self, k, v, t):
        if self.statsd_sock and self.name and t in self.statsd_types:
            name = self.get_metric_name(k)
            self.update_internal_stats(k, v)
            # beware, we are sending ms here, v is in s
            packet = '%s:%d|ms' % (name, v * 1000)
            self.send_metric(packet)


    def _encrypt(self, data):
        m = hashlib.md5()
        m.update(self.secret)
        key = m.hexdigest()

        m = hashlib.md5()
        m.update(self.secret + key)
        iv = m.hexdigest()

        data = pad(data)

        aes = AES.new(key, AES.MODE_CBC, iv[:16])

        encrypted = aes.encrypt(data)
        return base64.urlsafe_b64encode(encrypted)


    def reaper(self):
        while True:
            try:
                now = int(time.time())
                stats = self.stats
                self.stats = {}

                if len(stats) != 0:
                    s = ', '.join(['%s:%s' % (k, v) for (k, v) in stats.iteritems()])
                # If we are not in an initializer daemon we skip, we cannot have a real name, it sucks
                # to find the data after this
                if not self.is_shinkenio_enabled():
                    time.sleep(60)
                    continue

                metrics = []
                for (k, e) in stats.iteritems():
                    nk = '%s.%s.%s' % (self.type, self.name, k)
                    _min, _max, nb, _sum = e
                    _avg = float(_sum) / nb
                    # nb can't be 0 here and _min_max can't be None too
                    s = '%s.avg %f %d' % (nk, _avg, now)
                    metrics.append(s)
                    s = '%s.min %f %d' % (nk, _min, now)
                    metrics.append(s)
                    s = '%s.max %f %d' % (nk, _max, now)
                    metrics.append(s)
                    s = '%s.count %f %d' % (nk, nb, now)
                    metrics.append(s)

                # logger.debug('REAPER metrics to send %s (%d)' % (metrics, len(str(metrics))) )
                # get the inner data for the daemon
                struct = self.app.get_stats_struct()
                for metric in struct['metrics']:
                    name, val, ts, _ = metric
                    if "." in str(val):
                        # Value is a float
                        metrics.append('%s %f %d' % (name, val, ts))
                    else:
                        # Value is an integer
                        metrics.append('%s %d %d' % (name, val, ts))
                struct['metrics'] = metrics
                # logger.debug('REAPER whole struct %s' % struct)
                j = json.dumps(struct)
                if AES is not None and self.secret != '':
                    logger.debug('Stats PUT to kernel.shinken.io/api/v1/put/ with %s %s' % (
                        self.api_key, self.secret))

                    # assume a %16 length messagexs
                    encrypted_text = self._encrypt(j)
                    try:
                        self.con.put('/api/v1/put/?api_key=%s' % (
                                     self.api_key), encrypted_text)
                    except HTTPException, exp:
                        logger.error('Stats REAPER cannot put to the metric server %s' % exp)
            except Exception, e:
                logger.error(str(e))
                logger.debug(traceback.format_exc())
            time.sleep(60)


    def harvester(self):
        while True:
            try:
                if not self.is_statsd_enabled():
                    time.sleep(self.statsd_interval)
                    continue

                # During daemon config load operation, some attributes may not
                # have been initialized when we query stats_struct, so we
                # ignore AttributeError.
                try:
                    metrics = self.app.get_internal_metrics()
                except AttributeError:
                    time.sleep(self.statsd_interval)
                    continue

                for metric in metrics:
                    name, val, _type = metric
                    self.gauge(name, val, _type)
            except Exception, e:
                logger.error(str(e))
                logger.debug(traceback.format_exc())
            time.sleep(self.statsd_interval)


statsmgr = Stats()
