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

properties = {
    'daemons': ['broker'],
    'type': 'merlindb',
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    print "Get a Merlin broker for plugin %s" % plugin.get_name()
    print "Get backend", plugin.backend
    backend = plugin.backend

    # First try to import
    try:
        from merlindb_broker import Merlindb_broker
    except ImportError, exp:
        print "Warning: the plugin type %s is unavailable: %s" % (properties['type'], exp)
        return None


    # Now load the goo module for the backend
    if backend == 'mysql':
        try:
            host = plugin.host
            user = plugin.user
            password = plugin.password
            database = plugin.database
            if hasattr(plugin, 'character_set'):
                character_set = plugin.character_set
            else:
                character_set = 'utf8'

            instance = Merlindb_broker(plugin, backend, host=host, user=user, password=password, database=database, character_set=character_set)
            return instance

        except ImportError, exp:
            print "Warning: the plugin type %s is unavailable: %s" % (properties['type'], exp)
            return None

    if backend == 'sqlite':
        try:
            database_path = plugin.database_path
            instance = Merlindb_broker(plugin, backend, database_path=database_path)
            return instance

        except ImportError, exp:
            print "Warning: the plugin type %s is unavailable: %s" % (properties['type'], exp)
            return None

    print "Not creating a instance!!!"
    return None
