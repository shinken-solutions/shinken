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
import re
import sys

from thrift_broker import Thrift_broker, properties


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Thrift broker for plugin %s" % plugin.get_name()

    print plugin.__dict__
    # First try to import
    try:
        from thrift_broker import Thrift_broker
    except ImportError, exp:
        print "Warning: the plugin type %s is unavailable: %s" % ('thrift', exp)
        return None

    if hasattr(plugin, 'host'):
        if plugin.host == '*':
            host = ''
        else:
            host = plugin.host
    else:
        host = '127.0.0.1'

    if hasattr(plugin, 'port') and plugin.port != 'none':
        port = int(plugin.port)
    else:
        port = None

    if hasattr(plugin, 'socket') and plugin.socket != 'none':
        socket = plugin.socket
    else:
        socket = None

    if hasattr(plugin, 'allowed_hosts'):
        ips = [ip.strip() for ip in plugin.allowed_hosts.split(',')]
        allowed_hosts = [ip for ip in ips if re.match(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip)]
        if len(ips) != len(allowed_hosts):
            print "Warning: the list of allowed hosts is invalid"
            return None
    else:
        allowed_hosts = []

    if hasattr(plugin, 'database_file'):
        database_file = plugin.database_file
    else:
        database_file = os.path.join(os.path.abspath('.'), 'var', 'thrift.db')


    if hasattr(plugin, 'max_logs_age'):
        maxmatch = re.match(r'^(\d+)([dwm])$', plugin.max_logs_age)
        if maxmatch is None:
            print 'Warning: wrong format for max_logs_age. Must be <number>[d|w|m|y] or <number>'
            return None
        else:
            if not maxmatch.group(2):
                max_logs_age = int(maxmatch.group(1))
            elif maxmatch.group(2) == 'd':
                max_logs_age = int(maxmatch.group(1))
            elif maxmatch.group(2) == 'w':
                max_logs_age = int(maxmatch.group(1)) * 7
            elif maxmatch.group(2) == 'm':
                max_logs_age = int(maxmatch.group(1)) * 31
            elif maxmatch.group(2) == 'y':
                max_logs_age = int(maxmatch.group(1)) * 365
    else:
        max_logs_age = 365

    if hasattr(plugin, 'pnp_path'):
        pnp_path = plugin.pnp_path
    else:
        pnp_path = ''

    debug = getattr(plugin, 'debug', None)
    debug_queries = (getattr(plugin, 'debug_queries', '0') == '1')

    instance = Thrift_broker(plugin, host, port, socket, allowed_hosts, database_file, max_logs_age, pnp_path, debug, debug_queries)
    return instance
