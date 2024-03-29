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

from __future__ import absolute_import, division, print_function, unicode_literals

import six


class DB(object):
    """DB is a generic class for SQL Database"""

    def __init__(self, table_prefix=''):
        self.table_prefix = table_prefix

    def create_insert_query(self, table, data):
        """Create a INSERT query in table with all data of data (a dict)"""
        query = "INSERT INTO %s " % (self.table_prefix + table)
        props_str = ' ('
        values_str = ' ('
        i = 0  # f or the ',' problem... look like C here...
        for prop in sorted(data.keys()):
            i += 1
            val = data[prop]
            # Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0

            if i == 1:
                props_str = props_str + "%s " % prop
                values_str = values_str + "'%s' " % val
            else:
                props_str = props_str + ", %s " % prop
                values_str = values_str + ", '%s' " % val

        # Ok we've got data, let's finish the query
        props_str = props_str + ' )'
        values_str = values_str + ' )'
        query = query + props_str + ' VALUES' + values_str
        return query

    def create_update_query(self, table, data, where_data):
        """Create a update query of table with data, and use where data for
        the WHERE clause
        """
        query = "UPDATE %s set " % (self.table_prefix + table)

        # First data manage
        query_follow = ''
        i = 0  # for the , problem...
        for prop in sorted(data.keys()):
            # Do not need to update a property that is in where
            # it is even dangerous, will raise a warning
            if prop in where_data:
                continue
            i += 1
            val = data[prop]
            # Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0

            if i == 1:
                query_follow += "%s='%s' " % (prop, val)
            else:
                query_follow += ", %s='%s' " % (prop, val)

        # Ok for data, now WHERE, same things
        where_clause = " WHERE "
        i = 0  # For the 'and' problem
        for prop in sorted(where_data.keys()):
            i += 1
            val = where_data[prop]
            # Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0

            if i == 1:
                where_clause += "%s='%s' " % (prop, val)
            else:
                where_clause += "and %s='%s' " % (prop, val)

        query = query + query_follow + where_clause
        return query

    def fetchone(self):
        """Just get an entry"""
        return self.db_cursor.fetchone()

    def fetchall(self):
        """Get all entry"""
        return self.db_cursor.fetchall()
