#!/usr/bin/env python
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


#This class is an application for launch actions
#like notifications or event handlers
#The actionner listen configuration from Arbiter in a port (first argument)
#the configuration gived by arbiter is schedulers where actionner will take
#actions.
#When already launch and have a conf, actionner still listen to arbiter (one
#a timeout) if arbiter wants it to have a new conf, actionner forgot old
#chedulers (and actions into) take new ones and do the (new) job.


from shinken.satellite import Satellite
from shinken.property import PathProp, IntegerProp


#Our main APP class
class Reactionner(Satellite):
    do_checks = False # I do not do checks
    do_actions = True # just actions like notifications

    properties = Satellite.properties.copy()
    properties.update({
        'pidfile':   PathProp(default='reactionnerd.pid'),
        'port':      IntegerProp(default='7769'),
        'local_log': PathProp(default='reactionnerd.log'),
    })

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
        super(Reactionner, self).__init__('reactionner', config_file, is_daemon, do_replace, debug, debug_file)
