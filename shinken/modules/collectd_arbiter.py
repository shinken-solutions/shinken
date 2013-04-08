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
import time

from itertools import izip
from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand
from shinken.log import logger

properties = {
    'daemons': ['arbiter', 'receiver'],
    'type': 'collectd',
    'external': True,
    }

DEFAULT_PORT = 25826
DEFAULT_MULTICAST_IP = "239.192.74.66"
BUFFER_SIZE = 4096

# called by the plugin manager to get a broker
def get_instance(plugin):
    if hasattr(plugin, "multicast"):
        multicast = plugin.multicast.lower() in ("yes", "true", "1")
    else:
        multicast = False

    if hasattr(plugin, 'host'):
        host = plugin.host      
    else:
        host = DEFAULT_MULTICAST_IP
        multicast = True
    
    if hasattr(plugin, 'port'):
        port = int(plugin.port)
    else:
        port = DEFAULT_PORT


    logger.info("[Collectd] Using host=%s port=%d multicast=%d" % (host, port, multicast))

    instance = Collectd_arbiter(plugin, host, port, multicast)
    return instance

import socket
import struct
import time
from StringIO import StringIO


# Collectd message types
TYPE_HOST            = 0x0000
TYPE_TIME            = 0x0001
TYPE_TIME_HR         = 0x0008
TYPE_PLUGIN          = 0x0002
TYPE_PLUGIN_INSTANCE = 0x0003
TYPE_TYPE            = 0x0004
TYPE_TYPE_INSTANCE   = 0x0005
TYPE_VALUES          = 0x0006
TYPE_INTERVAL        = 0x0007
TYPE_INTERVAL_HR     = 0x0009
TYPE_MESSAGE         = 0x0100
TYPE_SEVERITY        = 0x0101

# DS kinds
DS_TYPE_COUNTER = 0
DS_TYPE_GAUGE = 1
DS_TYPE_DERIVE = 2
DS_TYPE_ABSOLUTE = 3

header = struct.Struct("!2H")
number = struct.Struct("!Q")
short  = struct.Struct("!H")
double = struct.Struct("<d")

elements = {}


def decode_values(pktype, plen, buf):
    nvalues = short.unpack_from(buf, header.size)[0]
    off = header.size + short.size + nvalues
    valskip = double.size

    # check the packet head
    if ((valskip + 1) * nvalues + short.size + header.size) != plen:
        return []
    if double.size != number.size:
        return []

    result = []
    for dstype in map(ord, buf[header.size + short.size:off]):
        if (dstype == DS_TYPE_COUNTER or dstype == DS_TYPE_DERIVE or dstype == DS_TYPE_ABSOLUTE):
            v = (dstype, number.unpack_from(buf, off)[0])
            result.append(v)
            off += valskip
        elif dstype == DS_TYPE_GAUGE:
            v = (dstype, double.unpack_from(buf, off)[0])
            result.append(v)
            off += valskip
        else:
            logger.warning("[Collectd] DS type %i unsupported" % dstype)

    return result


# Get a u64
def decode_number(pktype, pklen, buf):
    return number.unpack_from(buf, header.size)[0]


# Get a simple char
def decode_string(msgtype, pklen, buf):
    return buf[header.size:pklen-1]

# Mapping of message types to decoding functions.
decoder_mapping = {
    TYPE_VALUES: decode_values,
    TYPE_TIME: decode_number,
    TYPE_TIME_HR: decode_number,
    TYPE_INTERVAL: decode_number,
    TYPE_INTERVAL_HR: decode_number,
    TYPE_HOST: decode_string,
    TYPE_PLUGIN: decode_string,
    TYPE_PLUGIN_INSTANCE: decode_string,
    TYPE_TYPE: decode_string,
    TYPE_TYPE_INSTANCE: decode_string,
    TYPE_MESSAGE: decode_string,
    TYPE_SEVERITY: decode_number,
}



def decode_packet(buf):
    off = 0
    buflen = len(buf)
    while off < buflen:
        pktype, pklen = header.unpack_from(buf, off)

        if pklen > buflen - off:
            raise ValueError("Packet too long?")

        if pktype not in decoder_mapping:
            raise ValueError("Message type %i not recognized" % pktype)

        v = decoder_mapping[pktype](pktype, pklen, buf[off:])
        yield pktype, v
        off += pklen


class Data(list, object):
    def __init__(self, **kw):
        self.kind = 0
        self.time = 0
        self.interval = 0
        self.host = None
        self.plugin = ''
        self.plugininstance = ''
        self.type = ''
        self.typeinstance = ''
        self.message = ''
        self.severity = 0
        self.values = []

    def __str__(self):
        return "[%i] %s" % (self.time, self.values)

    def get_srv_desc(self):
        r = self.plugin
        if self.plugininstance:
            r += '-' + self.plugininstance
        return r

    def get_message(self):
        return self.message

    def get_kind(self):
        return self.kind

    def get_metric_name(self):
        r = self.type
        if self.typeinstance:
            r += '-' + self.typeinstance
        return r

    def get_metric_values(self):
        if len(self.values) == 0:
            return None
        return self.values

    def get_name(self):
        if not self.host:
            return None
        srv_desc = self.get_srv_desc()
        r = '%s;%s' % (self.host, srv_desc)
        return r

    def get_time(self):
        return self.time

    def get_message_command(self):
        now = int(time.time())
        if self.severity == 4: # OK
            returncode = 0
        elif self.severity == 1:
            returncode = 2
        elif self.severity == 2:
            returncode = 1
        else:
            returncode = 3
        return  '[%d] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s' % (now, self.host, self.get_srv_desc(), returncode, self.message)


class CollectdServer(object):
    def __init__(self, host, port, multicast):
        self.host = host
        self.port = port

        logger.info("[Collectd] Opening socket")
        family, socktype, proto, _, sockaddr = socket.getaddrinfo(
                None if multicast else self.host, self.port,
                socket.AF_UNSPEC, socket.SOCK_DGRAM, 0, socket.AI_PASSIVE)[0]

        self._sock = socket.socket(family, socktype, proto)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(sockaddr)
        logger.info("[Collectd] Socket open")

        if multicast:
            if hasattr(socket, "SO_REUSEPORT"):
                self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

            val = struct.pack("4sl", socket.inet_aton(self.host), socket.INADDR_ANY)

            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, val)
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        logger.info("[Collectd] Socket is opened")

    def interpret_opcodes(self, iterable):
        d = Data()

        for kind, data in iterable:
            d.kind = kind
            if kind == TYPE_TIME:
                d.time = data
            elif kind == TYPE_TIME_HR:
                d.time = data >> 30
            elif kind == TYPE_INTERVAL:
                d.interval = data
            elif kind == TYPE_INTERVAL_HR:
                d.interval = data >> 30
            elif kind == TYPE_HOST:
                d.host = data
            elif kind == TYPE_PLUGIN:
                d.plugin = data
            elif kind == TYPE_PLUGIN_INSTANCE:
                d.plugininstance = data
            elif kind == TYPE_TYPE:
                d.type = data
            elif kind == TYPE_TYPE_INSTANCE:
                d.typeinstance = data
            elif kind == TYPE_VALUES:
                d.values = data
            elif kind == TYPE_MESSAGE:
                d.message = data
            elif kind == TYPE_SEVERITY:
                d.severity = data
            yield d

    def receive(self):
        return self._sock.recv(BUFFER_SIZE)

    def decode(self, buf=None):
        if buf is None:
            buf = self.receive()
        return decode_packet(buf)

    def read(self, iterable=None):
        if iterable is None:
            iterable = self.decode()
        if isinstance(iterable, basestring):
            iterable = self.decode(iterable)
        return self.interpret_opcodes(iterable)


class Element(object):
    def __init__(self, host_name, sdesc, interval):
        self.host_name = host_name
        self.sdesc = sdesc
        self.perf_datas = {}
        self.last_update = 0.0
        self.interval = interval
        self.got_new_data = False

    def add_perf_data(self, mname, mvalues, mtime):
        if not mvalues:
            return

        r = []
        if mname not in self.perf_datas:
            for (dstype, newrawval) in mvalues:
                r.append((dstype, newrawval, newrawval, mtime))
        else:
            oldvalues = self.perf_datas[mname]

            for (olddstype,oldrawval,oldval,oldtime),(dstype,newrawval) in izip(oldvalues, mvalues):
                difftime = mtime - oldtime
                if difftime < 1:
                    continue
                if dstype == DS_TYPE_COUNTER or dstype == DS_TYPE_DERIVE or dstype == DS_TYPE_ABSOLUTE:
                    r.append((dstype,newrawval,(newrawval-oldrawval)/float(difftime),mtime))
                elif dstype == DS_TYPE_GAUGE:
                    r.append((dstype,newrawval,newrawval,mtime))

        self.perf_datas[mname] = r
        self.got_new_data = True

    def get_command(self):
        if len(self.perf_datas) == 0:
            return None

        if not self.got_new_data:
            return None

        now = int(time.time())
        if now > self.last_update + self.interval:
            r = '[%d] PROCESS_SERVICE_OUTPUT;%s;%s;CollectD| ' % (now, self.host_name, self.sdesc)
            for (k, v) in self.perf_datas.iteritems():
                for i, w in enumerate(v):
                  if len(v) > 1:
                      r += '%s_%d=%s ' % (k, i, str(w[2]))
                  else:
                      r += '%s=%s ' % (k, str(w[2]))
            print 'Updating', (self.host_name, self.sdesc)
#            self.perf_datas.clear()
            self.last_update = now
            self.got_new_data = False
            return r


class Collectd_arbiter(BaseModule):
    def __init__(self, modconf, host, port, multicast):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port
        self.multicast = multicast

    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        self.set_proctitle(self.name)
        self.set_exit_handler()
	
        try:
            cs = CollectdServer(self.host, self.port, self.multicast)
            while True:
                # Each second we are looking at sending old elements
                for e in elements.values():
                    c = e.get_command()
                    if c is not None:
                        print 'Got ', c
                        self.from_q.put(ExternalCommand(c))
                for item in cs.read():
                    print item, item.__dict__
                    n = item.get_name()
                    if n and n not in elements:
                        e = Element(item.host, item.get_srv_desc(), item.interval)
                        elements[n] = e
                    e = elements[n]
                    if item.get_kind() == TYPE_VALUES:
                        e.add_perf_data(item.get_metric_name(), item.get_metric_values(), item.get_time())
                    elif item.get_kind() == TYPE_MESSAGE:
                        c = item.get_message_command()
                        if c is not None:
                            self.from_q.put(ExternalCommand(c))
        except Exception, e:
            logger.error("[Collectd] exception: %s" % str(e))
        except ValueError, exp:
            logger.error("[Collectd] Read error: %s" % exp)


