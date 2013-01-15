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

import os

properties = {
    'daemons': ['broker'],
    'type': 'ndodb_oracle',
    'phases': ['running'],
    }


# called by the plugin manager to get a broker
def get_instance(plugin):
    # Try to import all need modules
    try:
        from ndodb_oracle_broker import Ndodb_Oracle_broker
    except ImportError, exp:
        print "Warning: the plugin type ndodb_oracle is unavailable: %s" % exp
        return None
    print "Get a ndoDB broker for plugin %s" % plugin.get_name()
    # TODO: catch errors
    if hasattr(plugin, 'oracle_home'):
        os.environ['ORACLE_HOME'] = plugin.oracle_home
        print "INFO: setting Oracle_HOME:", plugin.oracle_home

    user = plugin.user
    password = plugin.password
    database = plugin.database
    instance = Ndodb_Oracle_broker(plugin, user, password, database)
    return instance
