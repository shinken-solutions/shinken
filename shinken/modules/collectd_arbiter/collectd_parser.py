#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim: fileencoding=utf-8
#
# Copyright © 2009 Adrian Perez <aperez@igalia.com>
#
# Distributed under terms of the GPLv2 license.

#
# Updated by Rami Sayar for Collectd 5.1. Added DERIVE handling.
# Updated by Grégory Starck with few enhancements.
#  - notably possibility to subclass Values and Notification.

"""
Collectd network protocol implementation.
"""

import socket
import struct

from datetime import datetime
from copy import deepcopy


#############################################################################

DEFAULT_PORT = 25826
"""Default port"""

DEFAULT_IPv4_GROUP = "239.192.74.66"
"""Default IPv4 multicast group"""

DEFAULT_IPv6_GROUP = "ff18::efc0:4a42"
"""Default IPv6 multicast group"""

#############################################################################s

# https://collectd.org/wiki/index.php/Binary_protocol
# -> Protocol structure
# " The maximum length of payload in any part is therefore 65531 bytes. "
_BUFFER_SIZE = 65535 # 65535 > 65531, ok we are safe.

#############################################################################s

class CollectdException(Exception):
    pass

class CollectdValueError(CollectdException, ValueError):
    pass

class CollectdDecodeError(CollectdValueError):
    pass

class CollectdUnsupportedDSType(CollectdValueError):
    pass

class CollectdUnsupportedMessageType(CollectdValueError):
    pass

class CollectdBufferOverflow(CollectdValueError):
    pass

#############################################################################s

# Message kinds
TYPE_HOST            = 0x0000
TYPE_TIME            = 0x0001
TYPE_PLUGIN          = 0x0002
TYPE_PLUGIN_INSTANCE = 0x0003
TYPE_TYPE            = 0x0004
TYPE_TYPE_INSTANCE   = 0x0005
TYPE_VALUES          = 0x0006
TYPE_INTERVAL        = 0x0007
TYPE_TIMEHR          = 0x0008
TYPE_INTERVALHR      = 0x0009

# For notifications
TYPE_MESSAGE         = 0x0100
TYPE_SEVERITY        = 0x0101

#
TYPE_SIGN_SHA256     = 0x0200
TYPE_ENCR_AES256     = 0x0210


# DS kinds
DS_TYPE_COUNTER      = 0
DS_TYPE_GAUGE        = 1
DS_TYPE_DERIVE       = 2
DS_TYPE_ABSOLUTE     = 3

header = struct.Struct("!2H")
number = struct.Struct("!Q")
signed_number = struct.Struct("!q") # DERIVE are signed long longs
short  = struct.Struct("!H")
double = struct.Struct("<d")


assert double.size == number.size == signed_number.size == 8

#############################################################################s

_values_header_size = header.size + short.size
_single_value_size = 1 + 8 # 1 byte for type, 8 bytes for value


_ds_type_decoder = {
    DS_TYPE_COUNTER:    number,
    DS_TYPE_ABSOLUTE:   number,
    DS_TYPE_DERIVE:     signed_number,
    DS_TYPE_GAUGE:      double
}

def decode_network_values(ptype, plen, buf):
    """Decodes a list of DS values in collectd network format
    """
    assert ptype == TYPE_VALUES

    nvalues = short.unpack_from(buf, header.size)[0]
    values_tot_size = _values_header_size + nvalues * _single_value_size
    if values_tot_size != plen:
        raise CollectdValueError('Values total size != Part len (%s vs %s)' % (values_tot_size, plen))

    results = []
    off = _values_header_size + nvalues

    for dstype in map(ord, buf[_values_header_size:off]):
        try:
            decoder = _ds_type_decoder[dstype]
        except KeyError:
            raise CollectdUnsupportedDSType("DS type %i unsupported" % dstype)
        results.append((dstype, decoder.unpack_from(buf, off)[0]))
        off += 8
    return results


def decode_network_number(ptype, plen, buf):
    """Decodes a number (64-bit unsigned) in collectd network format.
    """
    return number.unpack_from(buf, header.size)[0]


def decode_network_string(ptype, plen, buf):
    """Decodes a string (\0 terminated) in collectd network format.
    :return: The string as bytes (not unicode).
    """
    return buf[header.size:plen-1]

# Mapping of message types to decoding functions.
_decoders = {
    TYPE_VALUES         : decode_network_values,
    TYPE_TIME           : decode_network_number,
    TYPE_INTERVAL       : decode_network_number,
    TYPE_HOST           : decode_network_string,
    TYPE_PLUGIN         : decode_network_string,
    TYPE_PLUGIN_INSTANCE: decode_network_string,
    TYPE_TYPE           : decode_network_string,
    TYPE_TYPE_INSTANCE  : decode_network_string,
    TYPE_MESSAGE        : decode_network_string,
    TYPE_SEVERITY       : decode_network_number,
    TYPE_TIMEHR         : decode_network_number,
    TYPE_INTERVALHR     : decode_network_number,
}


def decode_network_packet(buf):
    """Decodes a network packet in collectd format.
    """
    off = 0
    blen = len(buf)

    while off < blen:
        try:
            ptype, plen = header.unpack_from(buf, off)
        except struct.error as err:
            raise CollectdDecodeError(err)
        if not plen:
            raise CollectdValueError('Invalid part with size=0: buflen=%s off=%s ptype=%s' % (
                                      blen, off, ptype))

        rest = blen - off
        if plen > rest:
            raise CollectdBufferOverflow("Encoded part size greater than left amount of data in buffer: buflen=%s off=%s vsize=%s" % (
                blen, off, plen))

        try:
            decoder = _decoders[ptype]
        except KeyError:
            raise CollectdUnsupportedMessageType("Part type %s not recognized (off=%s)" % (ptype, off))

        try:
            res = decoder(ptype, plen, buf[off:])
        except struct.error as err:
            raise CollectdDecodeError(err)

        yield ptype, res
        off += plen

#############################################################################s

def cdtime_to_time(cdt):
    '''
    :param cdt: A CollectD Time or Interval HighResolution encoded value.
    :return: A float, representing a time EPOCH value, with up to nanosec after comma.
    '''
    # fairly copied from http://git.verplant.org/?p=collectd.git;a=blob;f=src/daemon/utils_time.h
    sec = cdt >> 30
    nsec = ((cdt & 0b111111111111111111111111111111) / 1.073741824) / 10**9
    assert 0 <= nsec < 1
    return sec + nsec


class Data(object):
    time = None
    interval = None
    host = None
    plugin = None
    plugininstance = None
    type = None
    typeinstance = None

    def __init__(self, **kw):
        for k,v in kw.iteritems():
            setattr(self, k, v)

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.time)

    @property
    def source(self):
        res = []
        if self.host:
            res.append(self.host)
        for attr in ('plugin', 'plugininstance', 'type', 'typeinstance'):
            val = getattr(self, attr)
            if val:
                res.append("/")
                res.append(val)
        return ''.join(res)

    def __str__(self):
        return "[%s] %s" % (self.time, self.source)



class Notification(Data):
    ''' Notification
    '''
    FAILURE  = 1
    WARNING  = 2
    OKAY     = 4

    SEVERITY = {
        FAILURE: "FAILURE",
        WARNING: "WARNING",
        OKAY   : "OKAY",
    }

    __severity = 0
    message  = ""

    def __set_severity(self, value):
        if value in (self.FAILURE, self.WARNING, self.OKAY):
            self.__severity = value

    severity = property(lambda self: self.__severity, __set_severity)

    @property
    def severitystring(self):
        return self.SEVERITY.get(self.severity, "UNKNOWN")

    def __str__(self):
        return "%s [%s] %s" % (
                super(Notification, self).__str__(),
                self.severitystring,
                self.message)



class Values(Data, list):
    ''' collectd Values ; contains a list of values associated with a particular collectd "element"
    '''
    def __str__(self):
        return "%s %s" % (Data.__str__(self), list.__str__(self))


#############################################################################s

class Parser(object):
    ''' Represent a collectd parser.

    Feed its `interpret´ method with some input and get Values or Notification instances.
    '''
    Values = Values # so to be able to customize their behavior
    Notification = Notification


    def receive(self):
        ''' Method used by the parser to get some data if you don't feed it explicitly with.
        If you want to make use of it you have to subclass and define it respecting the return format.
        :return: a 2-tuple : (buffer_read, address_read_from)
        The address_read_from format isn't enforced.
        '''
        raise NotImplementedError

    def decode(self, buf=None):
        """Decodes a given buffer or the next received packet from `receive()´.
        :return: a generator yielding 2-tuples (type, value).
        """
        if buf is None:
            buf, addr_from = self.receive()
        return decode_network_packet(buf)


    def interpret_opcodes(self, iterable):
        '''
        :param iterable: An iterable of 2-tuples (type, value).
        :return: A generator yielding Values or Notification instances based on the iterable.
        :raise: The generator, when yielding results, can raise a CollectdException (or subclass)
                instance if there is a decode error.
        '''
        vl = self.Values() # ; assert isinstance(vl, Values)
        nt = self.Notification() # ; assert isinstance(nt, Notification)

        for kind, data in iterable:

            if kind == TYPE_TIME:
                vl.time = nt.time = data
            elif kind == TYPE_TIMEHR:
                vl.time = nt.time = cdtime_to_time(data)
            elif kind == TYPE_INTERVAL:
                vl.interval = data
            elif kind == TYPE_INTERVALHR:
                vl.interval = cdtime_to_time(data)
            elif kind == TYPE_HOST:
                vl.host = nt.host = data
            elif kind == TYPE_PLUGIN:
                vl.plugin = nt.plugin = data
            elif kind == TYPE_PLUGIN_INSTANCE:
                vl.plugininstance = nt.plugininstance = data
            elif kind == TYPE_TYPE:
                vl.type = nt.type = data
            elif kind == TYPE_TYPE_INSTANCE:
                vl.typeinstance = nt.typeinstance = data
            elif kind == TYPE_SEVERITY:
                nt.severity = data
            elif kind == TYPE_MESSAGE:
                nt.message = data
                yield deepcopy(nt)
            elif kind == TYPE_VALUES:
                vl[:] = data
                yield deepcopy(vl)
            # others kinds are just ignored for now.
            # it's permitted by collectd packet format so to be extensible.


    def interpret(self, input=None):
        """Interprets an explicit or implicit `input´ "sequence" if given.

        :param input:
            If None or not given -> A fresh packet will be read from the socket. Then the packet will be decode().
            If a basestring -> It will also be decode().

            After what the result of decode() (a generator which yields 2-tuple(value_type, value)) is given
            to interpret_opcodes() which will then yield collectd `Values´ or `Notification´ instances.

            If the `input´ initial value isn't None nor a basestring then it's directly given to
            interpret_opcodes(), you have to make sure the `input´ has the correct format.

        :return: A generator yielding collectd `Values´ or `Notification´ instances.

        :raise:
            When a read on the socket is needed, it's not impossible to raise some IO exception.
            Otherwise no raise should occur to return the generator.
            But the returned generator can raise (subclass-)`CollectdException´ instance if a decode problem occurs.
        """
        if isinstance(input, (type(None), basestring)):
            input = self.decode(input)
        return self.interpret_opcodes(input)



class Reader(Parser):
    """Network reader for collectd data.

    Listens on the network in a given address, which can be a multicast
    group address, and handles reading data when it arrives.
    """

    def __init__(self, host=None, port=DEFAULT_PORT, multicast=False):
        '''
        :param host: An host IP address. If not given or None -> multicast is forced enabled.
        :param port: The port to listen. Defaults to collectd default port.
        :param multicast: By default False. If truth value -> multicast is enabled.
        :return: A ready to be used collectd Reader instance.
        '''
        if host is None:
            multicast = True
            host = DEFAULT_IPv4_GROUP

        self.host, self.port = host, port
        self.ipv6 = ":" in self.host

        family, socktype, proto, canonname, sockaddr = socket.getaddrinfo(
                None if multicast else self.host, self.port,
                socket.AF_INET6 if self.ipv6 else socket.AF_UNSPEC,
                socket.SOCK_DGRAM, 0, socket.AI_PASSIVE)[0]

        self._sock = socket.socket(family, socktype, proto)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(sockaddr)

        if multicast:
            if hasattr(socket, "SO_REUSEPORT"):
                self._sock.setsockopt(
                        socket.SOL_SOCKET,
                        socket.SO_REUSEPORT, 1)

            val = None
            if family == socket.AF_INET:
                assert "." in self.host
                val = struct.pack("4sl",
                        socket.inet_aton(self.host), socket.INADDR_ANY)
            elif family == socket.AF_INET6:
                raise NotImplementedError("IPv6 support not ready yet")
            else:
                raise ValueError("Unsupported network address family")

            self._sock.setsockopt(
                    socket.IPPROTO_IPV6 if self.ipv6 else socket.IPPROTO_IP,
                    socket.IP_ADD_MEMBERSHIP, val)
            self._sock.setsockopt(
                    socket.IPPROTO_IPV6 if self.ipv6 else socket.IPPROTO_IP,
                    socket.IP_MULTICAST_LOOP, 0)


    def receive(self):
        """ Receives a single raw collectd network packet. """
        return self._sock.recvfrom(_BUFFER_SIZE)


    def close(self):
        self._sock.close()

