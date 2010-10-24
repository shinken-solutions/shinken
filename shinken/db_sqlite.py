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


#DBSqlite is a sqlite access database class
from db import DB
import copy
import sqlite3


class DBSqlite(DB):
    def __init__(self, db_path, table_prefix = ''):
        self.table_prefix = table_prefix
        self.db_path = db_path


    #Create the database connexion
    def connect_database(self):
        self.db = sqlite3.connect(self.db_path)
        self.db_cursor = self.db.cursor ()


    #Just run the query
    def execute_query(self, query):
        print "[SqliteDB]I run query", query, "\n"
        self.db_cursor.execute(query)
        self.db.commit ()
