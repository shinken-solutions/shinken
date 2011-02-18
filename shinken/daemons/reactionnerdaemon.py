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
from shinken.util import to_int, to_bool


#Our main APP class
class Reactionner(Satellite):
    do_checks = False # I do not do checks
    do_actions = True # just actions like notifications

    properties = {
            'workdir' : {'default' : '/usr/local/shinken/var', 'pythonize' : None, 'path' : True},
            'pidfile' : {'default' : '/usr/local/shinken/var/reactionnerd.pid', 'pythonize' : None, 'path' : True},
            'port' : {'default' : '7769', 'pythonize' : to_int},
            'host' : {'default' : '0.0.0.0', 'pythonize' : None},
            'user' : {'default' : 'shinken', 'pythonize' : None},
            'group' : {'default' : 'shinken', 'pythonize' : None},
            'idontcareaboutsecurity' : {'default' : '0', 'pythonize' : to_bool},
            'use_ssl' : {'default' : '0', 'pythonize' : to_bool},
            'certs_dir' : {'default' : 'etc/certs', 'pythonize' : None},
            'ca_cert' : {'default' : 'etc/certs/ca.pem', 'pythonize' : None},
            'server_cert' : {'default': 'etc/certs/server.pem', 'pythonize' : None},
            'hard_ssl_name_check' : {'default' : '0', 'pythonize' : to_bool},
            'use_local_log' : {'default' : '0', 'pythonize' : to_bool},
            'local_log' : {'default' : '/usr/local/shinken/var/reactionnerd.log', 'pythonize' : None, 'path' : True},
    }

    def __init__(self, config_file, is_daemon, do_replace, debug, debug_file):
        Satellite.__init__(self, 'reactionner', config_file, is_daemon, do_replace, debug, debug_file)
