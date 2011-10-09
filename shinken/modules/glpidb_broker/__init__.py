#!/usr/bin/python
#Copyright (C) 2011 Durieux David, d.durieux@siprossii.com
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
print "I am GlpiDB Broker"

properties = {
    'daemons' : ['broker'],
    'type' : 'glpidb',
    'phases' : ['running'],
    }


#called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Glpi broker for plugin %s" % plugin.get_name()

    #First try to import
    try:
        from glpidb_broker import Glpidb_broker
    except ImportError , exp:
        print "Warning : the plugin type %s is unavailable : %s" % (properties['type'], exp)
        return None


    #Now load the goo module for the backend
    try:
        host = plugin.host
        user = plugin.user
        password = plugin.password
        database = plugin.database
        if hasattr( plugin, 'character_set'):
            character_set = plugin.character_set
        else:
            character_set = 'utf8'

        instance = Glpidb_broker(plugin, host=host, user=user, password=password, database=database, character_set=character_set)
        return instance
    except ImportError , exp:
        print "Warning : the plugin type %s is unavailable : %s" % (properties['type'], exp)
        return None

    print "Not creating a instance!!!"
    return None
