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
from shinken.log import logger

properties = {
    'daemons': ['arbiter'],
    'type': 'hack_poller_tag_by_macros',
    'external': False,
    'phases': ['late_configuration'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Hack pollertag by macros module for plugin %s" % plugin.get_name()
    instance = Hack_pt_by_macros(plugin)
    return instance


# Just print some stuff
class Hack_pt_by_macros(BaseModule):
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)
        self.host_macro_name = mod_conf.host_macro_name
        self.service_macro_name = mod_conf.service_macro_name

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "Initilisation of the hack poller tag by macro module"

    def hook_late_configuration(self, arb):
        logger.info("[HackPollerTagByMacros in hook late config")
        for h in arb.conf.hosts:
            if h.poller_tag == 'None' and self.host_macro_name.upper() in h.customs:
                v = h.customs[self.host_macro_name.upper()]
                # We should tag the host, but also the command because this phase is
                # after the automatic command inheritance
                h.poller_tag = v
                h.check_command.poller_tag = v
        for s in arb.conf.services:
            if s.poller_tag == 'None' and self.service_macro_name.upper() in s.customs:
                v = s.customs[self.service_macro_name.upper()]
                s.poller_tag = v
                s.check_command.poller_tag = v
