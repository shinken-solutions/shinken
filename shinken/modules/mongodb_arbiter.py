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


"""
This module job is to get configuration data (mostly hosts) from a mongodb database.
"""

#This module imports hosts and services configuration from a MySQL Database
#Queries for getting hosts and services are pulled from shinken-specific.cfg configuration file.

from pymongo.connection import Connection

from shinken.basemodule import BaseModule


properties = {
    'daemons' : ['arbiter'],
    'type' : 'mongodb',
    'external' : False,
    'phases' : ['configuration'],
}

# called by the plugin manager to get a module instance
def get_instance(plugin):
    print "[MongoDB Importer Module] : Get Mongodb importer instance for plugin %s" % plugin.get_name()
    uri   = plugin.uri
    database = plugin.database

    instance = Mongodb_arbiter(plugin, uri, database)
    return instance

# Retrieve hosts from a Mongodb
class Mongodb_arbiter(BaseModule):
    def __init__(self, mod_conf, uri, database):
        BaseModule.__init__(self, mod_conf)
        self.uri        = uri
        self.database   = database
        # Some used varaible init
        self.con = None
        self.db = None


    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "[Mongodb Importer Module] : Try to open a Mongodb connection to %s:%s" % (self.uri, self.database)
        try:
            self.con = Connection(self.uri)
            self.db = getattr(self.con, self.database)
        except Exception, e:
            print "Mongodb Module : Error %s:" % e
            raise
        print "[Mongodb Importer Module] : Connection OK"


    # Main function that is called in the CONFIGURATION phase
    def get_objects(self):
        if not self.db:
            print "[Mongodb Importer Module] : Problem during init phase"
            return {}

        r = {'hosts' : []}

        cur = self.db.hosts.find({})
        for h in cur:
            print "DBG: mongodb: get host", h
            # We remove a mongodb specific property, the _id
            del h['_id']
            # And we add an imported_from property to say it came from
            # mongodb
            h['imported_from'] = 'mongodb:%s:%s' % (self.uri, self.database)
            r['hosts'].append(h)

        return r
