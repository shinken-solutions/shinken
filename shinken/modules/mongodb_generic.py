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
This module job is to get configuration data (mostly hosts) from a mongodb database.
"""

# This module imports hosts and services configuration from a MySQL Database
# Queries for getting hosts and services are pulled from shinken-specific.cfg configuration file.

from pymongo.connection import Connection

from shinken.basemodule import BaseModule

properties = {
    'daemons': ['arbiter', 'webui', 'skonf'],
    'type': 'mongodb',
    'external': False,
    'phases': ['configuration'],
}


# called by the plugin manager to get a module instance
def get_instance(plugin):
    print "[MongoDB Module]: Get Mongodb instance for plugin %s" % plugin.get_name()
    uri = plugin.uri
    database = plugin.database

    instance = Mongodb_generic(plugin, uri, database)
    return instance


# Retrieve hosts from a Mongodb
class Mongodb_generic(BaseModule):
    def __init__(self, mod_conf, uri, database):
        BaseModule.__init__(self, mod_conf)
        self.uri = uri
        self.database = database
        # Some used varaible init
        self.con = None
        self.db = None

    # Called by Arbiter to say 'let's prepare yourself guy'
    def init(self):
        print "[Mongodb Module]: Try to open a Mongodb connection to %s:%s" % (self.uri, self.database)
        try:
            self.con = Connection(self.uri)
            self.db = getattr(self.con, self.database)
        except Exception, e:
            print "Mongodb Module: Error %s:" % e
            raise
        print "[Mongodb Module]: Connection OK"

################################ Arbiter part #################################

    # Main function that is called in the CONFIGURATION phase
    def get_objects(self):
        if not self.db:
            print "[Mongodb Module]: Problem during init phase"
            return {}

        r = {}

        tables = ['hosts', 'services', 'contacts', 'commands', 'timeperiods']
        for t in tables:
            r[t] = []

            cur = getattr(self.db, t).find({'_state': {'$ne': 'disabled'}})
            for h in cur:
                print "DBG: mongodb: get an ", t, h
                # We remove a mongodb specific property, the _id
                del h['_id']
                # And we add an imported_from property to say it came from
                # mongodb
                h['imported_from'] = 'mongodb:%s:%s' % (self.uri, self.database)
                r[t].append(h)

        return r

#################################### WebUI parts ############################

    # We will get in the mongodb database the user preference entry, for the 'shinken-global' user
    # and get the key they are asking us
    def get_ui_common_preference(self, key):
        if not self.db:
            print "[Mongodb]: error Problem during init phase"
            return None

        e = self.db.ui_user_preferences.find_one({'_id': 'shinken-global'})

        print '[Mongodb] Get entry?', e
        # Maybe it's a new entryor missing this parameter, bail out
        if not e or not key in e:
            print '[Mongodb] no key or invalid one'
            return None

        return e.get(key)
        
    # We will get in the mongodb database the user preference entry, and get the key
    # they are asking us
    
    def get_ui_user_preference(self, user, key):
        if not self.db:
            print "[Mongodb]: error Problem during init phase"
            return None

        if not user:
            print '[Mongodb]: error get_ui_user_preference::no user'
            return None
        # user.get_name()
        e = self.db.ui_user_preferences.find_one({'_id': user.get_name()})

        print '[Mongodb] Get entry?', e
        # Maybe it's a new entryor missing this parameter, bail out
        if not e or not key in e:
            print '[Mongodb] no key or invalid one'
            return None

        return e.get(key)

    # Same but for saving
    def set_ui_user_preference(self, user, key, value):
        if not self.db:
            print "[Mongodb]: error Problem during init phase"
            return None

        if not user:
            print '[Mongodb]: error get_ui_user_preference::no user'
            return None

        # Ok, go for update

        # check a collection exist for this user
        u = self.db.ui_user_preferences.find_one({'_id': user.get_name()})
        if not u:
            # no collection for this user? create a new one
            print "[Mongodb] No user entry for %s, I create a new one" % user.get_name()
            self.db.ui_user_preferences.save({'_id': user.get_name(), key: value})
        else:
            # found a collection for this user
            print "[Mongodb] user entry found for %s" % user.get_name()

        print '[Mongodb]: saving user pref', "'$set': { %s: %s }" % (key, value)
        r = self.db.ui_user_preferences.update({'_id': user.get_name()}, {'$set': {key: value}})
        print "[Mongodb] Return from update", r
        # Mayeb there was no doc there, if so, create an empty one
        if not r:
            # Maybe the user exist, if so, get the whole user entry
            u = self.db.ui_user_preferences.find_one({'_id': user.get_name()})
            if not u:
                print "[Mongodb] No user entry for %s, I create a new one" % user.get_name()
                self.db.ui_user_preferences.save({'_id': user.get_name(), key: value})
            else:  # ok, it was just the key that was missing, just update it and save it
                u[key] = value
                print '[Mongodb] Just saving the new key in the user pref'
                self.db.ui_user_preferences.save(u)
