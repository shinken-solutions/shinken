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

from shinken.log import logger

properties = {
    'daemons': ['arbiter'],
    'type': 'ip_tag',
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info("[IP Tag] Get a Service Perfdata broker for plugin %s" % plugin.get_name())

    # First try to import
    try:
        from ip_tag_arbiter import Ip_Tag_Arbiter
    except ImportError, exp:
        logger.warning("[IP Tag] Warning: the plugin type %s is unavailable: %s" % ('ip_tag', exp))
        return None

    # Catch errors
    ip_range = plugin.ip_range
    prop = plugin.property
    value = plugin.value
    method = getattr(plugin, 'method', 'replace')

    instance = Ip_Tag_Arbiter(plugin, ip_range, prop, value, method)
    return instance
