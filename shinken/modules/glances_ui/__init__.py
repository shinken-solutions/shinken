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

# This Class implement the Thrift Service Check Acceptor, an NSCA inspired
# interface to submit checks results


import os

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['webui'],
    'type': 'glances_ui',
    'external': False,
    }


from glances_ui import Glances_UI

# called by the plugin manager to get a broker
def get_instance(mod_conf):
    logger.info("[Glances WebUI] Get a Glances WebUI module for plugin %s" % mod_conf.get_name())
    instance = Glances_UI(mod_conf)
    return instance

