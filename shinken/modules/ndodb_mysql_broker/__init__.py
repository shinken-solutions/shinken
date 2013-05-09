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

import sys

from ndodb_mysql_broker import Ndodb_Mysql_broker, properties, _mysql_exceptions
from shinken.log import logger


# called by the plugin manager to get a instance
def get_instance(mod_conf):

    logger.debug("Get a ndoDB instance for plugin %s" % mod_conf.get_name())

    if not _mysql_exceptions:
        raise Exception('Cannot load module python-mysqldb. Please install it.')

    # Default behavior: character_set is utf8 and synchro is turned off
    if not hasattr(mod_conf, 'character_set'):
        mod_conf.character_set = 'utf8'
    if not hasattr(mod_conf, 'synchronize_database_id'):
        mod_conf.synchronize_database_id = '1'
    instance = Ndodb_Mysql_broker(mod_conf)

    return instance
