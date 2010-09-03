#!/usr/bin/env python
#Copyright (C) 2009-2010 : 
#    Gabes Jean, naparuba@gmail.com 
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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


#DB is a generic class for SQL Database

class DB(object):
    def __init__(self, table_prefix = ''):
        self.table_prefix = table_prefix
    

    #Create a INSERT query in table with all data of data (a dict)
    def create_insert_query(self, table, data):
        query = "INSERT INTO %s " % (self.table_prefix + table)
        props_str = ' ('
        values_str = ' ('
        i = 0 #for the ',' problem... look like C here...
        for prop in data:
            i += 1
            val = data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0
            if isinstance(val, unicode):
                val = val.encode('utf-8').replace("'", "''")
            else:
                val = str(val)
            if i == 1:
                props_str = props_str + "%s " % prop
                values_str = values_str + "'%s' " % val
            else:
                props_str = props_str + ", %s " % prop
                values_str = values_str + ", '%s' " % val

        #Ok we've got data, let's finish the query
        props_str = props_str + ' )'
        values_str = values_str + ' )'
        query = query + props_str + ' VALUES' + values_str
        return query


    #Create a update query of table with data, and use where data for
    #the WHERE clause
    def create_update_query(self, table, data, where_data):
        query = "UPDATE %s set " % (self.table_prefix + table)

        #First data manage
        query_folow = ''
        i = 0 #for the , problem...
        for prop in data:
            i += 1
            val = data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0
            if i == 1:
                query_folow += "%s='%s' " % (prop, str(val).replace("'", "''"))
            else:
                query_folow += ", %s='%s' " % (prop, str(val).replace("'", "''"))

        #Ok for data, now WHERE, same things
        where_clause = " WHERE "
        i = 0 # For the 'and' problem
        for prop in where_data:
            i += 1
            val = where_data[prop]
            #Boolean must be catch, because we want 0 or 1, not True or False
            if isinstance(val, bool):
                if val:
                    val = 1
                else:
                    val = 0
            if i == 1:
                where_clause += "%s='%s' " % (prop, val)
            else:
                where_clause += "and %s='%s' " % (prop, val)

        query = query + query_folow + where_clause
        return query


    #Just get an entry
    def fetchone(self):
        return self.db_cursor.fetchone()
