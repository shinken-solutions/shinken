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


# This text is print at the import
from shinken.log import logger

properties = {
    'daemons': ['broker'],
    'type': 'glpidb',
    'phases': ['running'],
    }

# called by the plugin manager to get a broker
def get_instance(plugin):
    logger.info("[GLPIdb Broker] Get a Glpi broker for plugin %s" % plugin.get_name())

    # First try to import
    try:
        from glpidb_broker import Glpidb_broker
    except ImportError, exp:
        logger.warning("[GLPIdb Broker] Warning: the plugin type %s is unavailable: %s" % (properties['type'], exp))
        return None


    # Now load the goo module for the backend
    try:
        host = plugin.host
        user = plugin.user
        password = plugin.password
        database = plugin.database
        if hasattr(plugin, 'character_set'):
            character_set = plugin.character_set
        else:
            character_set = 'utf8'

        instance = Glpidb_broker(plugin, host=host, user=user, password=password, database=database, character_set=character_set)
        return instance
    except ImportError, exp:
        logger.warning("[GLPIdb Broker] Warning: the plugin type %s is unavailable: %s" % (properties['type'], exp))
        return None

    logger.error("[GLPIdb Broker] Not creating a instance!!!")
    return None
