#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

import MySQLdb
from MySQLdb import IntegrityError
from MySQLdb import ProgrammingError


from shinken.db import DB
from shinken.log import logger

class DBMysql(DB):
    """DBMysql is a MySQL access database class"""

    def __init__(self, host, user, password, database, character_set,
                 table_prefix='', port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.character_set = character_set
        self.table_prefix = table_prefix
        self.port = port

    def connect_database(self):
        """Create the database connection
        TODO: finish (begin :) ) error catch and conf parameters...
        Import to catch exception
        """

        # self.db = MySQLdb.connect (host = "localhost", user = "root",
        #                            passwd = "root", db = "merlin")
        self.db = MySQLdb.connect(host=self.host, user=self.user,
                                  passwd=self.password, db=self.database,
                                  port=self.port)
        self.db.set_character_set(self.character_set)
        self.db_cursor = self.db.cursor()
        self.db_cursor.execute('SET NAMES %s;' % self.character_set)
        self.db_cursor.execute('SET CHARACTER SET %s;' % self.character_set)
        self.db_cursor.execute('SET character_set_connection=%s;' %
                               self.character_set)
        # Thanks:
        # http://www.dasprids.de/blog/2007/12/17/python-mysqldb-and-utf-8
        # for utf8 code :)

    def execute_query(self, query, do_debug=False):
        """Just run the query
        TODO: finish catch
        """
        if do_debug:
            logger.debug("[MysqlDB]I run query %s", query)
        try:
            self.db_cursor.execute(query)
            self.db.commit()
            return True
        except IntegrityError, exp:
            logger.warning("[MysqlDB] A query raised an integrity error: %s, %s", query, exp)
            return False
        except ProgrammingError, exp:
            logger.warning("[MysqlDB] A query raised a programming error: %s, %s", query, exp)
            return False
