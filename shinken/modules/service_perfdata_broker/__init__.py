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

properties = {
    'daemons': ['broker'],
    'type': 'service_perfdata',
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Service Perfdata broker for plugin %s" % plugin.get_name()

    # First try to import
    try:
        from service_perfdata_broker import Service_perfdata_broker
    except ImportError, exp:
        print "Warning: the plugin type %s is unavailable: %s" % ('service_perfdata', exp)
        return None

    # Catch errors
    path = plugin.path
    if hasattr(plugin, 'mode'):
        mode = plugin.mode
    else:
        mode = 'a'

    if hasattr(plugin, 'template'):
        template = plugin.template
    else:
        template = "$LASTSERVICECHECK$\t$HOSTNAME$\t$SERVICEDESC$\t$SERVICEOUTPUT$\t$SERVICESTATE$\t$SERVICEPERFDATA$\n"
        # int(data['last_chk']),data['host_name'], data['service_description'], data['output'], current_state, data['perf_data']

    instance = Service_perfdata_broker(plugin, path, mode, template)
    return instance
