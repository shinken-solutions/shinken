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
    'daemons': ['broker', 'scheduler'],
    'type': 'livestatus',
    'phases': ['running'],
    'external': True,
    }

from livestatus_broker import LiveStatus_broker
# called by the plugin manager to get an instance


def get_instance(plugin):
    logger.info("[Livestatus Broker] Get a Livestatus instance for plugin %s" % plugin.get_name())

    # First try to import
    try:
        from livestatus_broker import LiveStatus_broker
    except ImportError, exp:
        logger.warning("[Livestatus Broker] Warning: the plugin type %s is unavailable: %s" % ('livestatus', exp))
        return None

    instance = LiveStatus_broker(plugin)
    return instance
