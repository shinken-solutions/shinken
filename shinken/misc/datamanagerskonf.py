#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
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

from shinken.util import safe_print
from shinken.misc.datamanager import DataManager

class FakeRegenerator(object):
    def __init__(self):
        return


class DataManagerSKonf(DataManager):
    def __init__(self):
        self.rg = FakeRegenerator()
        self.db = None

    def load_conf(self, cfg):
        ts = ['hosts', 'services', 'contacts', 'timeperiods', 'commands']
        for t in ts:
            v = getattr(cfg, t)
            setattr(self.rg, t, v)

    # Get an object and return a dict with it's properties
    def unclass(self, o):
        d = {}
        if o is None:
            return d

        # Get even a partial dict of object properties
        properties = o.__class__.properties
        for prop in properties:
            if hasattr(o, prop):
                d[prop] = getattr(o, prop)
        customs = getattr(o, 'customs', [])
        for (k,v) in customs.iteritems():
            print "SET CUSTOM", k, v
            d[k] = v
        # Inner object are NOT ediable by skonf!
        d['editable'] = '0'
        return d


    def load_db(self, db):
        self.db = db


    def get_in_db(self, table, key, value):
        col = getattr(self.db, table)
        print "Looking for", key, value, "in", table, col
        r = col.find_one({key : value})
        print "Founded", r
        return r

    def get_all_in_db(self, table):
        col = getattr(self.db, table)
        print "GET ALL FROM", table, col
        r = col.find({})
        print "Founded", r
        return r

    # Merge internal and db hosts in the same list
    def get_hosts(self):
        r = []
        for h in self.rg.hosts:
            v = self.unclass(h)
            print "Unclass", v
            r.append(v)
        names = [h['host_name'] for h in r if 'host_name' in h]
        for h in self.get_all_in_db('hosts'):
            if not h.get('host_name', '') in names:
                r.append(h)

        return r


    def get_contact(self, cname):
        for c in self.rg.contacts:
            print "DUMP RAW CONTACT", c, c.__dict__
        r = self.rg.contacts.find_by_name(cname)
        if r:
            r = self.unclass(r)
            print "Will finallyu give un unclass", r
            return r
        r = self.get_in_db('contacts', 'contact_name', cname)
        return r


    def get_host(self, hname):
        for c in self.rg.hosts:
            print "DUMP RAW HOST", c, c.__dict__
        r = self.rg.hosts.find_by_name(hname)
        if r:
            r = self.unclass(r)
            print "Will finallyu give un unclass", r
            return r
        r = self.get_in_db('hosts', 'host_name', hname)
        return r

        

datamgr = DataManagerSKonf()
