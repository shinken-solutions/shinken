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



#This text is print at the import
print "I am Couchdb Broker"

properties = {
    'type' : 'couchdb',
    }

#called by the plugin manager to get a broker
def get_broker(plugin):

    print "Get a Couchdb broker for plugin %s" % plugin.get_name()

    #first try the import
    try:
        from couchdb_broker import Couchdb_broker
    except ImportError as exp:
        print "Warning : the plugin type %s is unavalable : %s" % (get_type(), exp)
        return None

    #TODO : catch errors
    host = plugin.host
    user = plugin.user
    password = plugin.password
    broker = Couchdb_broker(plugin.get_name(), host, user, password)
    return broker


def get_type():
    return properties['type']
