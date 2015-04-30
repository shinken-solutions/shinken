#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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

import time

from shinken.basemodule import BaseModule
from shinken.external_command import ExternalCommand
from shinken.log import logger

properties = {
    'daemons': ['arbiter'],
    'type': 'dummy_arbiter',
    'external': True,
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info("[Dummy Arbiter] Get a Dummy arbiter module for plugin %s", plugin.get_name())
    instance = Dummy_arbiter(plugin)
    return instance


# Just print some stuff
class Dummy_arbiter(BaseModule):
    def __init__(self, mod_conf):
        BaseModule.__init__(self, mod_conf)

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[Dummy Arbiter] Initialization of the dummy arbiter module")
        #self.return_queue = self.properties['from_queue']


    # Ok, main function that is called in the CONFIGURATION phase
    def get_objects(self):
        logger.info("[Dummy Arbiter] Ask me for objects to return")
        r = {'hosts': []}
        h = {'name': 'dummy host from dummy arbiter module',
             'register': '0',
             }

        r['hosts'].append(h)
        r['hosts'].append({
                            'host_name': "dummyhost1",
                            'use': 'linux-server',
                            'address': 'localhost'
                            })
        logger.info("[Dummy Arbiter] Returning to Arbiter the hosts: %s", str(r))

        return r

    def hook_late_configuration(self, conf):
        logger.info("[Dummy Arbiter] Dummy in hook late config")

    def do_loop_turn(self):
        logger.info("[Dummy Arbiter] Raise a external command as example")
        e = ExternalCommand('Viva la revolution')
        self.from_q.put(e)
        time.sleep(1)
