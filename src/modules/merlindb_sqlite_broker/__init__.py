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
print "I am Merlin Sqlite Broker"


properties = {
    'type' : 'merlindb_sqlite',
    }


#called by the plugin manager to get a broker
def get_broker(plugin):
    print "Get a Merlin sqlite broker for plugin %s" % plugin.get_name()

    #First try to import
    try:
        from merlindb_sqlite_broker import Merlindb_sqlite_broker
    except ImportError as exp:
        print "Warning : the plugin type %s is unavalable : %s" % (get_type(), exp)
        return None

   #TODO : catch errors
    database_path = plugin.database_path
    broker = Merlindb_sqlite_broker(plugin.get_name(), database_path)
    return broker


def get_type():
    return properties['type']

