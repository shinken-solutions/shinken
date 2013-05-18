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

"""
This class store log broks in a black hole
It is one possibility (!) for an exchangeable storage for log broks
"""

from shinken.log import logger
from shinken.basemodule import BaseModule

properties = {
    'daemons': ['livestatus'],
    'type': 'logstore_null',
    'external': False,
    'phases': ['running'],
    }


# called by the plugin manager
def get_instance(plugin):
    logger.info("[Logstore Null] Get an LogStore Null module for plugin %s" % plugin.get_name())
    instance = LiveStatusLogStoreNull(plugin)
    return instance


class LiveStatusLogStoreNull(BaseModule):

    def __init__(self, modconf):
        BaseModule.__init__(self, modconf)
        self.plugins = []

    def load(self, app):
        self.app = app

    def init(self):
        pass

    def open(self):
        logger.info("[Logstore Null] Open LiveStatusLogStoreNull ok")

    def close(self):
        pass

    def commit(self):
        pass

    def commit_and_rotate_log_db(self):
        pass

    def manage_log_brok(self, b):
        # log brok successfully stored in the black hole
        pass

    def add_filter(self, operator, attribute, reference):
        pass

    def add_filter_and(self, andnum):
        pass

    def add_filter_or(self, ornum):
        pass

    def add_filter_not(self):
        pass

    def get_live_data_log(self):
        """Like get_live_data, but for log objects"""
        result = []
        return result
