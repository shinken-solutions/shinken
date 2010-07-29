#!/usr/bin/python
#Copyright (C) 2009 Gabes Jean, naparuba@gmail.com
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


#This Class is a plugin for the Shinken Broker. It is in charge
#to brok information into the merlin database. for the moment
#only Mysql is supported. This code is __imported__ from Broker.
#The managed_brok function is called by Broker for manage the broks. It calls
#the manage_*_brok functions that create queries, and then run queries.


import copy
import sqlite3


#Class for the Merlindb Broker
#Get broks and puts them in merlin database
class Sqlite_backend:
    def __init__(self, database_path):
        self.database_path = database_path

    def init(self):
        self.connect_database()
    

    #Create the database connexion
    #TODO : finish (begin :) ) error catch and conf parameters...
    def connect_database(self):
        self.db = sqlite3.connect(self.database_path)
        #self.db.set_character_set(self.character_set)
        self.db_cursor = self.db.cursor ()
        #self.db_cursor.execute('SET NAMES %s;' % self.character_set)
        #self.db_cursor.execute('SET CHARACTER SET %s;' % self.character_set)
        #self.db_cursor.execute('SET character_set_connection=%s;' % self.character_set)


    #Just run the query
    #TODO: finish catch
    def execute_query(self, query):
        print "[SqliteBackend]I run query", query, "\n"
        #try:
        self.db_cursor.execute(query)
        self.db.commit ()
        #except IntegrityError as exp:
        #    print "[Merlindb] Warning : a query raise an integrity error : %s, %s" % (query, exp) 
        #except ProgrammingError as exp:
        #    print "[Merlindb] Warning : a query raise a programming error : %s, %s" % (query, exp) 
        

    #Create a INSERT query in table with all data of data (a dict)
    def create_insert_query(self, table, data):
        query = "INSERT INTO %s " % table
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
        query = query + props_str + 'VALUES' + values_str
        return query

    
    #Create a update query of table with data, and use where data for
    #the WHERE clause
    def create_update_query(self, table, data, where_data):
        query = "UPDATE %s set " % table
		
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
