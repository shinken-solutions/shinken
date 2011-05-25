#!/usr/bin/python
# -*- coding: utf-8 -*-
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

#This module imports hosts and services configuration from a MySQL Database
#Queries for getting hosts and services are pulled from shinken-specific.cfg configuration file.

import MySQLdb

from shinken.basemodule import BaseModule

#This text is print at the import
print "Detected module : MySQL importer for Arbiter"

properties = {
    'daemons' : ['arbiter'],
    'type' : 'mysql_import',
    'external' : False,
    'phases' : ['configuration'],
}

#called by the plugin manager to get a broker
def get_instance(plugin):
    print "[MySQL Importer Module] : Get MySQL importer instance for plugin %s" % plugin.get_name()
    host = plugin.host
    login = plugin.login
    password = plugin.password
    database = plugin.database
    reqhosts = plugin.reqhosts
    reqservices = plugin.reqservices
    instance = MySQL_importer_arbiter(plugin, host, login, password, database,reqhosts,reqservices)
    return instance

#Retrieve hosts from a MySQL database
class MySQL_importer_arbiter(BaseModule):
    def __init__(self, mod_conf, host, login, password, database, reqhosts,reqservices):
        BaseModule.__init__(self, mod_conf)
        self.host  = host
        self.login = login
        self.password = password
        self.database = database
        self.reqhosts = reqhosts
        self.reqservices = reqservices

    #Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "[MySQL Importer Module] : Try to open a MySQL connection to %s" % self.host
        try:
            self.conn = MySQLdb.connect (host = self.host,
                        user = self.login,
                        passwd = self.password,
                        db = self.database)
        except MySQLdb.Error, e:
            print "MySQL Module : Error %d: %s" % (e.args[0], e.args[1])
            raise
        print "[MySQL Importer Module] : Connection opened"

    #Main function that is called in the CONFIGURATION phase
    def get_objects(self):
        if not hasattr(self, 'conn'):
            print "[MySQL Importer Module] : Problem during init phase"
            return {}

        r = {'hosts' : []}
        result_set = {}

        cursor = self.conn.cursor (MySQLdb.cursors.DictCursor)
        print "[MySQL Importer Module] : getting hosts configuration from database"
        try:
            cursor.execute (self.reqhosts)
            result_set = cursor.fetchall ()
        except MySQLdb.Error, e:
            print "MySQL Module : Error %d: %s" % (e.args[0], e.args[1])

        for row in result_set:
            h = {}
            for column in row:
                if row[column]:
                    h[column]= row[column]
            r['hosts'].append(h)

        print "[MySQL Importer Module] : getting services configuration from database"
        r['services'] = []

        try:
            cursor.execute (self.reqservices)
            result_set = cursor.fetchall ()
        except MySQLdb.Error, e:
            print "MySQL Module : Error %d: %s" % (e.args[0], e.args[1])

        for row in result_set:
            h = {}
            for column in row:
                if row[column]:
                    h[column]= row[column]
            r['services'].append(h)

        cursor.close ()
        self.conn.close ()
        del self.conn

        print "[MySQL Importer Module] : Returning to Arbiter the object:", r
        return r
