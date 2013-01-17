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

# This Class is an example of a broker  module

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'dummy_broker',
    'external': False,
    }


# called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info("[Dummy Broker] Get a Dummy broker module for plugin %s" % mod_conf.get_name())
    instance = Dummy_broker(mod_conf)
    return instance


# Just print some stuff
class Dummy_broker(BaseModule):

    def __init__(self, mod_conf, foo):
        BaseModule.__init__(self, mod_conf)


    # Called by Broker to say 'let's prepare yourself guy'
    def init(self):
        logger.info("[Dummy Broker] Initialization of the dummy broker module")


      
    # An host check have just arrived, we UPDATE data info with this                                                                                                      
#    def manage_brok(self, b):
#        #Do things
#        pass
    
