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

from shinken.satellite import Satellite
from shinken.property import PathProp, IntegerProp


# Our main APP class
class Poller(Satellite):
    do_checks = True    # I do checks
    do_actions = False  # but no actions
    my_type = 'poller'

    properties = Satellite.properties.copy()
    properties.update({
        'pidfile':   PathProp(default='pollerd.pid'),
        'port':      IntegerProp(default=7771),
        'local_log': PathProp(default='pollerd.log'),
    })

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file, profile):
        super(Poller, self).__init__('poller', config_file, is_daemon, do_replace, debug,
                                     debug_file)
