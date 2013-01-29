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


# This Class is an NSCA Arbiter module
# Here for the configuration phase AND running one

import time
import select
import socket
import struct
import random

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand
from shinken.log import logger

properties = {
    'daemons': ['arbiter', 'receiver'],
    'type': 'nsca_server',
    'external': True,
    'phases': ['running'],
    }


def decrypt_xor(data, key):
    keylen = len(key)
    crypted = [chr(ord(data[i]) ^ ord(key[i % keylen]))
            for i in xrange(len(data))]
    return ''.join(crypted)


def get_instance(plugin):
    """ Return a module instance for the plugin manager """
    logger.info("Get a NSCA arbiter module for plugin %s" % plugin.get_name())

    if hasattr(plugin, 'host'):
        if plugin.host == '*':
            host = ''
        else:
            host = plugin.host
    else:
        host = '127.0.0.1'

    if hasattr(plugin, 'port'):
        port = int(plugin.port)
    else:
        port = 5667

    if hasattr(plugin, 'encryption_method'):
        encryption_method = int(plugin.encryption_method)
    else:
        encryption_method = 0

    if hasattr(plugin, 'password'):
        password = plugin.password
    else:
        password = ""

    if password == "" and encryption_method != 0:
        logger.error("[NSCA] No password specified whereas there is a encryption_method defined")
        logger.warning("[NSCA] Setting password to dummy to avoid crash!")
        password = "dummy"

    if hasattr(plugin, 'max_packet_age'):
        max_packet_age = min(plugin.max_packet_age, 900)
    else:
        max_packet_age = 30

    instance = NSCA_arbiter(plugin, host, port,
            encryption_method, password, max_packet_age)
    return instance


class NSCA_arbiter(BaseModule):
    """Please Add a Docstring to describe the class here"""

    def __init__(self, modconf, host, port, encryption_method, password, max_packet_age):
        BaseModule.__init__(self, modconf)
        self.host = host
        self.port = port
        self.encryption_method = encryption_method
        self.password = password
        self.rng = random.Random(password)
        self.max_packet_age = max_packet_age

    def send_init_packet(self, sock):
        '''
        Build an init packet
         00-127: IV
         128-131: unix timestamp
        '''
        iv = ''.join([chr(self.rng.randrange(256)) for i in xrange(128)])
        init_packet = struct.pack("!128sI", iv, int(time.time()))
        sock.send(init_packet)
        return iv

    def read_check_result(self, data, iv):
        '''
        Read the check result

        The !hhIIh64s128s512sh is the description of the packet.
        See Python doc for details. This is equivalent to the figure below

        00-01      Version           02-03 Padding
        04-07      CRC32
        08-11      Timestamp
        12-13      Return Code       14-15 Hostname
        16-75      Hostname
        76-77      Hostname           78-79 Service name
        80-203     Service name
        204-205 Service name      206-207 Service output
        208-715 Service output
        716-717 Service output    718-719 Padding
        '''
        if len(data) != 720:
            return None

        if self.encryption_method == 1:
            data = decrypt_xor(data, self.password)
            data = decrypt_xor(data, iv)

        # version, pad1, crc32, timestamp, rc, hostname_dirty, service_dirty, output_dirty, pad2
        # are the name of var if needed later
        (_, _, _, timestamp, rc, hostname_dirty, service_dirty, output_dirty, _) = \
            struct.unpack("!hhIIh64s128s512sh", data)
        hostname = hostname_dirty.split("\0", 1)[0]
        service = service_dirty.split("\0", 1)[0]
        output = output_dirty.split("\0", 1)[0]
        return (timestamp, rc, hostname, service, output)

    def post_command(self, timestamp, rc, hostname, service, output):
        '''
        Send a check result command to the arbiter
        '''
        if len(service) == 0:
            extcmd = "[%lu] PROCESS_HOST_CHECK_RESULT;%s;%d;%s\n" % \
                (timestamp, hostname, rc, output)
        else:
            extcmd = "[%lu] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s\n" % \
                (timestamp, hostname, service, rc, output)

        e = ExternalCommand(extcmd)
        self.from_q.put(e)

    def process_check_result(self, databuffer, IV):
        (timestamp, rc, hostname, service, output) = self.read_check_result(databuffer, IV)
        current_time = time.time()
        check_result_age = current_time - timestamp
        if timestamp > current_time:
            logger.info("[NSCA] Dropping packet with future timestamp.")
        elif check_result_age > self.max_packet_age:
            logger.info(
                "[NSCA] Dropping packet with stale timestamp - packet was %s seconds old." % \
                check_result_age)
        else:
            self.post_command(timestamp, rc, hostname, service, output)

    # When you are in "external" mode, that is the main loop of your process
    def main(self):
        self.set_proctitle(self.name)

        self.set_exit_handler()
        backlog = 5
        size = 8192
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setblocking(0)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(backlog)
        input = [server]
        databuffer = {}
        IVs = {}

        while not self.interrupted:
            # outputready and exceptready unused
            inputready, _, _ = select.select(input, [], [], 1)
            for s in inputready:
                if s == server:
                    # handle the server socket
                    # address unused
                    client, _ = server.accept()
                    iv = self.send_init_packet(client)
                    IVs[client] = iv
                    input.append(client)
                else:
                    # handle all other sockets
                    try:
                        data = s.recv(size)
                    except:
                        continue
                    if len(data) == 0:
                        try:
                            # Closed socket
                            del databuffer[s]
                            del IVs[s]
                        except:
                            pass
                        s.close()
                        input.remove(s)
                        continue
                    if s in databuffer:
                        databuffer[s] += data
                    else:
                        databuffer[s] = data
                    while len(databuffer[s]) >= 720:
                        # end-of-transmission or an empty line was received
                        self.process_check_result(databuffer[s][0:720], IVs[s])
                        databuffer[s] = databuffer[s][720:]
