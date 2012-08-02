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

# This Class is an example of an Arbiter module
# Here for the configuration phase AND running one

import re
from shinken.basemodule import BaseModule

properties = {
    'daemons': ['arbiter'],
    'type': 'hack_commands_poller_tag',
    'external': False,
    'phases': ['late_configuration'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Hack commands pollertag module for plugin %s" % plugin.get_name()
    instance = Hack_cmds_pt(plugin)
    return instance


# Just print some stuff
class Hack_cmds_pt(BaseModule):
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.cmd_line_match = r"""%s""" % mod_conf.cmd_line_match
        self.poller_tag = mod_conf.poller_tag

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the hack commands poller tag module"
        #self.return_queue = self.properties['from_queue']


    # Now look at hosts and services, if they use our command we just changed
    # we must update their commandCall object too
    def update_service_and_hosts_commandCall(self, arb, cmd, tag):
        for h in arb.conf.hosts:
            if h.check_command.command == cmd:
                h.check_command.poller_tag = tag
        for s in arb.conf.services:
            if s.check_command.command == cmd:
                s.check_command.poller_tag = tag

    def hook_late_configuration(self, arb):
        print("[HackCmdPollerTag in hook late config")
        p = re.compile(self.cmd_line_match)
        for c in arb.conf.commands:
            m = p.match(c.command_line)
            if m is not None and c.poller_tag is 'None':
                #print "[Hack command poller tag] Match! Chaging the poller tag of %s by %s " % (c.command_name, self.poller_tag)
                c.poller_tag = self.poller_tag
                self.update_service_and_hosts_commandCall(arb, c, self.poller_tag)
