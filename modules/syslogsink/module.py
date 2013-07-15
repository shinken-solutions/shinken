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


# This Class is a plugin for the Shinken Broker. It is in charge
# to brok log into the syslog

import syslog
import types
from logging.handlers import SysLogHandler

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'syslog',
    'external': False,
    'phases': ['running'],
}


# called by the plugin manager to get a broker
def get_instance(plugin):
    name = plugin.get_name()
    logger.info("Get a Syslog broker for plugin %s" % (name))

    # syslog.syslog priority defaults to (LOG_INFO | LOG_USER)
    facility = syslog.LOG_USER
    priority = syslog.LOG_INFO

    # Get configuration values, if any
    if hasattr(plugin, 'facility'):
        facility = plugin.facility
    if hasattr(plugin, 'priority'):
        priority = plugin.priority

    # Ensure config values have a string type compatible with
    # SysLogHandler.encodePriority
    if type(facility) in types.StringTypes:
        facility = types.StringType(facility)
    if type(priority) in types.StringTypes:
        priority = types.StringType(priority)

    # Convert facility / priority (integers or strings) to aggregated
    # priority value
    sh = SysLogHandler()
    try:
        priority = sh.encodePriority(facility, priority)
    except TypeError, e:
        logger.error("[%s] Couldn't get syslog priority, "
                     "reverting to defaults" % (name))

    logger.debug("[%s] Syslog priority: %d" % (name, priority))

    instance = Syslog_broker(plugin, priority)
    return instance


# Class for the Syslog Broker
# Get log broks and send them to syslog
class Syslog_broker(BaseModule):
    def __init__(self, modconf, priority):
        BaseModule.__init__(self, modconf)
        self.priority = priority

    # A log has just arrived, we send it to syslog
    def manage_log_brok(self, b):
        data = b.data
        syslog.openlog("shinken")
        syslog.syslog(self.priority, data['log'].encode('UTF-8'))
