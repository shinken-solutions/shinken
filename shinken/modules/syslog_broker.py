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

from shinken.basemodule import BaseModule

properties = {
    'daemons': ['broker'],
    'type': 'syslog',
    'external': False,
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Syslog broker for plugin %s" % plugin.get_name()

    #Catch errors
    #path = plugin.path
    instance = Syslog_broker(plugin)
    return instance


# Class for the Merlindb Broker
# Get broks and puts them in merlin database
class Syslog_broker(BaseModule):
    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)

    # A service check have just arrived, we UPDATE data info with this
    def manage_log_brok(self, b):
        data = b.data
        syslog.syslog(data['log'].encode('UTF-8'))
