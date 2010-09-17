#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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

import os

#This text is print at the import
print "I am Livestatus Broker"


properties = {
    'type' : 'livestatus',
    'external' : True
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Livestatus broker for plugin %s" % plugin.get_name()

    print plugin.__dict__
    #First try to import
    try:
        from livestatus_broker import Livestatus_broker
    except ImportError , exp:
        print "Warning : the plugin type %s is unavalable : %s" % (get_type(), exp)
        return None

    if hasattr(plugin, 'host'):
        if plugin.host == '*':
            host = ''
        else:
            host = plugin.host
    else:
        host = '127.0.0.1'
    if hasattr(plugin, 'port'):
        port = int(plugin.port)
    else:
        port = 6557
    if hasattr(plugin, 'socket'):
        socket = plugin.socket
    else:
        socket = os.sep.join([os.path.abspath(''), 'var', 'rw', 'live'])
    if hasattr(plugin, 'database_file'):
        database_file = int(plugin.database_file)
    else:
        database_file = os.sep.join([os.path.abspath(''), 'var', 'livestatus.db'])

    instance = Livestatus_broker(plugin.get_name(), host, port, socket, database_file)
    return instance

