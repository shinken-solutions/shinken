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


from shinken.satellite import Satellite
from shinken.util import to_int, to_bool


#Our main APP class
class Poller(Satellite):
    do_checks = True    # I do checks
    do_actions = False  # but no actions
    
    properties = Satellite.properties.copy()
    properties.update({
        'pidfile':  {'default' : '/usr/local/shinken/var/pollerd.pid', 'pythonize' : None, 'path' : True},
        'port':     {'default' : '7771', 'pythonize' : to_int},
        'local_log': {'default' : '/usr/local/shinken/var/pollerd.log', 'pythonize' : None, 'path' : True},
    })

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
        Satellite.__init__(self, 'poller', config_file, is_daemon, do_replace, debug, debug_file)
