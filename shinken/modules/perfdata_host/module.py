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
# to brok information of the service perfdata into the file
# var/service-perfdata
# So it just manage the service_check_return
# Maybe one day host data will be useful too
# It will need just a new file, and a new manager :)

import codecs

from shinken.basemodule import BaseModule
from shinken.log import logger


properties = {
    'daemons': ['broker'],
    'type': 'host_perfdata',
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info("[Host Perfdata Broker] Get a Host Perfdata broker for plugin %s" % plugin.get_name())

    # Catch errors
    path = plugin.path
    if hasattr(plugin, 'mode'):
        mode = plugin.mode
    else:
        mode = 'a'

    if hasattr(plugin, 'template'):
        template = plugin.template
    else:
        template = "$LASTHOSTCHECK$\t$HOSTNAME$\t$HOSTOUTPUT$\t$HOSTSTATE$\t$HOSTPERFDATA$\n"
        # int(data['last_chk']),data['host_name'], data['service_description'], data['output'], current_state, data['perf_data']

    instance = Host_perfdata_broker(plugin, path, mode, template)
    return instance



# Class for the Merlindb Broker
# Get broks and puts them in merlin database
class Host_perfdata_broker(BaseModule):
    def __init__(self, modconf, path, mode, template):
        BaseModule.__init__(self, modconf)
        self.path = path
        self.mode = mode
        self.template = template

        # Make some raw change
        self.template = self.template.replace(r'\t', '\t')
        self.template = self.template.replace(r'\n', '\n')

        # In Nagios it's said to force a return in line
        if not self.template.endswith('\n'):
            self.template += '\n'

    # Called by Broker so we can do init stuff
    # TODO: add conf param to get pass with init
    # Conf from arbiter!
    def init(self):
        logger.info("[Host Perfdata broker] I open the host-perfdata file '%s'" % self.path)
        self.file = codecs.open(self.path, self.mode, "utf-8")

    # We've got a 0, 1, 2 or 3 (or something else? ->3
    # And want a real OK, WARNING, CRITICAL, etc...
    def resolve_host_state(self, state):
        states = {0: 'UP', 1: 'DOWN', 2: 'DOWN', 3: 'UNKNOWN'}
        if state in states:
            return states[state]
        else:
            return 'UNKNOWN'

    # A service check have just arrived, we UPDATE data info with this
    def manage_host_check_result_brok(self, b):
        data = b.data
        # The original model
        # "$TIMET\t$HOSTNAME\t$OUTPUT\t$SERVICESTATE\t$PERFDATA\n"
        current_state = self.resolve_host_state(data['state_id'])
        macros = {
            '$LASTHOSTCHECK$': int(data['last_chk']),
            '$HOSTNAME$': data['host_name'],
            '$HOSTOUTPUT$': data['output'],
            '$HOSTSTATE$': current_state,
            '$HOSTPERFDATA$': data['perf_data'],
            '$LASTHOSTSTATE$': data['last_state'],
            }
        s = self.template
        for m in macros:
            s = s.replace(m, unicode(macros[m]))
        #s = "%s\t%s\t%s\t%s\t%s\n" % (int(data['last_chk']),data['host_name'], \
        #                                  data['output'], \
        #                                  current_state, data['perf_data'] )
        self.file.write(s)
        self.file.flush()
