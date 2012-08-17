#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
# Gabes Jean, naparuba@gmail.com
# Gerhard Lausser, Gerhard.Lausser@consol.de
# Gregory Starck, g.starck@gmail.com
# Hartmut Goebel, h.goebel@goebel-consult.de
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken. If not, see <http://www.gnu.org/licenses/>.

"""
This module job is to get configuration data (hosts a/o WebUI user settings) from a sqlite database.
"""

import sys

old_implementation = False
try:
    import sqlite3
except ImportError:  # python 2.4 do not have it
    try:
        import pysqlite2.dbapi2 as sqlite3  # but need the pysqlite2 install from http://code.google.com/p/pysqlite/downloads/list
    except ImportError:  # python 2.4 do not have it
        import sqlite as sqlite3  # one last try
        old_implementation = True

from shinken.basemodule import BaseModule
from shinken.log import logger

properties = {
    'daemons': ['webui'],
    'type': 'sqlitedb',
    'external': False,
    'phases': [],
}


# called by the plugin manager to get a module instance
def get_instance(plugin):
    logger.debug("[SQLite Module]: Get instance for plugin %s" % plugin.get_name())
    if 'sqlite3' not in sys.modules:
        raise Exception('Cannot find the sqlite module. Please install it.')
    uri      = plugin.uri

    instance = SQLite_generic(plugin, uri)
    return instance


class SQLite_generic(BaseModule):
    def __init__(self, mod_conf, uri):
        BaseModule.__init__(self, mod_conf)
        self.uri = uri
        self.db  = None

    # Called by Arbiter to say 'let's prepare yourself guy'
    #TODO: create database & tables if not exists
    def init(self):
        logger.info("[SQLite Module]: Try to open SQLite database at %s" % (self.uri))
        try:
            self.db = sqlite3.connect(self.uri, check_same_thread=False)
        except Exception, e:
            logger.error("SQLitedb Module: Error %s:" % e)
            raise
        logger.info("[SQLite Module]: Opened connection to SQLite database OK"

        # initiate database tables if not exists
        self.db.execute("""CREATE TABLE IF NOT EXISTS ui_preferences (
            user TEXT, key TEXT, value TEXT, 
            PRIMARY KEY (user, key)
        )""")
        self.db.commit()

#################################### WebUI parts ############################

    # Query global preference entry from database (user is *shinken-global*)
    def get_ui_common_preference(self, key):
        return self._get_ui_user_preference('shinken-global', key)

    # Query user preference entre from database
    def get_ui_user_preference(self, user, key):
        if not self.db:
            logger.error("[SQLite]: Problem during init phase")
            return None

        if not user:
            logger.error("[SQLite]: error get_ui_user_preference::no user")
            return None

        return self._get_ui_user_preference(user.get_name(), key)
       
    def _get_ui_user_preference(self, user, key):
        curs = self.db.cursor()
        curs.execute("SELECT value FROM ui_preferences WHERE user=? AND key=?", (user, key))
        res = curs.fetchone()
        curs.close()

        # Maybe it's a new entryor missing this parameter, bail out
        if res is None:
            logger.warning('[SQLite] no key or invalid one')
            return None

        return res[0]

    # Same but for saving
    def set_ui_common_preference(self, key, value):
        return self._set_ui_user_preference('shinken-global', key, value)

    def set_ui_user_preference(self, user, key, value):
        if not user:
            logger.warning('[SQLite]: get_ui_user_preference::no user')
            return None

        return self._set_ui_user_preference(user.get_name(), key, value)

    def _set_ui_user_preference(self, user, key, value):
        if not self.db:
            logger.error("[SQLite]: Problem during init phase")
            return None

        self.db.execute("INSERT OR REPLACE INTO ui_preferences (user, key, value) VALUES (?,?,?)", (user, key, value))
        self.db.commit()
