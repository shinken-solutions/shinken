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

from db import DB
from shinken.log import logger
import sqlite3


class DBSqlite(DB):
    """DBSqlite is a sqlite access database class"""

    def __init__(self, db_path, table_prefix=''):
        self.table_prefix = table_prefix
        self.db_path = db_path

    def connect_database(self):
        """Create the database connection"""
        self.db = sqlite3.connect(self.db_path)
        self.db_cursor = self.db.cursor()

    def execute_query(self, query):
        """Just run the query"""
        logger.debug("[SqliteDB] Info: I run query '%s'", query)
        self.db_cursor.execute(query)
        self.db.commit()
