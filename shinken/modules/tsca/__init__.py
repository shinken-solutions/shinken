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

# This Class implement the Thrift Service Check Acceptor, an NSCA inspired
# interface to submit checks results

from shinken.log import logger

properties = {
    'daemons': ['arbiter', 'receiver'],
    'type': 'tsca_server',
    'external': True,
    'phases': ['running'],
    }


# called by the plugin manager to get an arbiter 
def get_instance(plugin):
    logger.debug("Get a TSCA arbiter module for plugin %s" % plugin.get_name())

    try:
        from tsca import TSCA_arbiter
    except ImportError, exp:
        logger.error("Warning: the plugin type %s is unavailable: %s" %
                ('TSCA', exp))
        return None

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
        port = 9090
    if hasattr(plugin, 'max_packet_age'):
        max_packet_age = min(plugin.max_packet_age, 900)
    else:
        max_packet_age = 30

    instance = TSCA_arbiter(plugin, host, port, max_packet_age)
    return instance
