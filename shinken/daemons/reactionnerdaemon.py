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



# This class is an application that launches actions for the schedulers
# Acions can be notifications or event handlers
# The actionner listens for the configuration from the Arbiter
# The configuration consists of a list of schedulers from which
# the Reactionner will launch actions for.
# When running the Reactionner can interact with the Arbiter in the following
# ways. Respond to Pyro pings from Arbiter, or receive a new configuration
# Reactionner will flush current actions on configuration reload.


from shinken.satellite import Satellite
from shinken.property import PathProp, IntegerProp


class Reactionner(Satellite):
    do_checks = False # I do not do checks
    do_actions = True

    properties = Satellite.properties.copy()
    properties.update({
        'pidfile':   PathProp(default='reactionnerd.pid'),
        'port':      IntegerProp(default='7769'),
        'local_log': PathProp(default='reactionnerd.log'),
    })

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
        super(Reactionner, self).__init__('reactionner', config_file, is_daemon, do_replace, debug, debug_file)
