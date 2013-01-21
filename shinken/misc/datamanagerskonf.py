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
        properties = o.__class__.properties.keys()
        # TODO: we can't add register to properties, find why
        properties.append('register')
        for prop in properties:
            if hasattr(o, prop):
                d[prop] = getattr(o, prop)
        customs = getattr(o, 'customs', {})
        for (k, v) in customs.iteritems():
            print "SET CUSTOM", k, v
            d[k] = v
        # Inner object are NOT editable by skonf!
        d['editable'] = '0'

        # For service we must set the _id like it should :)
        if o.__class__.my_type == 'service':
            print "SET AN INNER ID FOR", o.get_name(), o.id
            d['_id'] = 'inner-%s' % o.id

        return d

    def load_db(self, db):
        self.db = db

    def get_in_db(self, table, key, value):
        col = getattr(self.db, table)
        print "Looking for", key, value, "in", table, col
        r = col.find_one({key: value})
        print "Founded", r
        return r

    def get_all_in_db(self, table):
        col = getattr(self.db, table)
        print "GET ALL FROM", table, col
        r = col.find({})
        print "Founded", r
        return r

    def get_generics(self, table, key):
        r = []
        inners = getattr(self.rg, table)
        print "Got inners", inners, type(inners)
        for i in inners:
            print 'Unclassing', i
            v = self.unclass(i)
            print "Unclass", v
            r.append(v)
        # Get a lsit of the known elements
        names = [i[key] for i in r if key in i]
        for i in self.get_all_in_db(table):
            if not i.get(key, '') in names:
                r.append(i)
        return r

    # Merge internal and db hosts in the same list
    def get_hosts(self):
        return self.get_generics('hosts', 'host_name')

    def get_contacts(self):
        return self.get_generics('contacts', 'contact_name')

    def get_timeperiods(self):
        return self.get_generics('timeperiods', 'timeperiod_name')

    def get_commands(self):
        return self.get_generics('commands', 'command_name')

    def get_services(self):
        return self.get_generics('services', '_')

    # Get a specific object
    def get_contact(self, cname):
        for c in self.rg.contacts:
            print "DUMP RAW CONTACT", c, c.__dict__
        r = self.rg.contacts.find_by_name(cname)
        if r:
            r = self.unclass(r)
            print "Will finally give an unclass", r
            return r
        r = self.get_in_db('contacts', 'contact_name', cname)
        return r

    def get_host(self, hname):
        for c in self.rg.hosts:
            print "DUMP RAW HOST", c, c.__dict__
        r = self.rg.hosts.find_by_name(hname)
        if r:
            r = self.unclass(r)
            print "Will finally give an unclass", r
            return r
        r = self.get_in_db('hosts', 'host_name', hname)
        return r

    def get_command(self, cname):
        for c in self.rg.commands:
            print "DUMP RAW COMMAND", c, c.__dict__
        r = self.rg.commands.find_by_name(cname)
        if r:
            r = self.unclass(r)
            print "Will finally give un unclass", r
            return r
        r = self.get_in_db('commands', 'command_name', cname)
        return r

    def get_timeperiod(self, cname):
        for c in self.rg.timeperiods:
            print "DUMP RAW COMMAND", c, c.__dict__
        r = self.rg.timeperiods.find_by_name(cname)
        if r:
            r = self.unclass(r)
            print "Will finally give un unclass", r
            return r
        r = self.get_in_db('timeperiods', 'timeperiod_name', cname)
        return r

    # Ok for service there is a trick. A service got by default
    # no KEY, so we got ids and uuid with inner-ID or uuid
    def get_service(self, name):
        if name.startswith('inner-'):
            _id = name[6:]
            print "New name for search service", _id
            s = self.rg.services[int(_id)]
            s = self.unclass(s)
            return s
        print "OK search the service uuid", name, "in the database"
        r = self.get_in_db('services', '_id', name)
        return r

    def build_pack_tree(self, packs):

        # dirname sons packs
        t = ('', [], [])
        for p in packs:
            path = p.path
            dirs = path.split('/')
            dirs = [d for d in dirs if d != '']
            pos = t
            for d in dirs:
                print "In the level", d, " and the context", pos
                sons = pos[1]
                print "Get the sons to add me", sons

                if not d in [s[0] for s in sons]:
                    print "Add a new level"
                    print "Get the sons to add me", sons
                    node = (d, [], [])
                    sons.append(node)
                # Ok now search the node for d and take it as our new position
                for s in sons:
                    if s[0] == d:
                        print "We found our new position", s
                        pos = s

            # Now add our pack to this entry
            print "Add pack to the level", pos[0]
            pos[2].append(p)
        print "The whole pack tree", t
        return t

    def get_pack_tree(self, packs):
        t = self.build_pack_tree(packs)
        r = self._get_pack_tree(t)
        print "RETURN WHOLE PACK TREE", r
        return r

    def _get_pack_tree(self, tree):
        print "__get_pack_tree:: for", tree
        name = tree[0]
        sons = tree[1]
        packs = tree[2]

        # Sort our sons by they names
        def _sort(e1, e2):
            if e1[0] < e2[0]:
                return -1
            if e1[0] > e2[0]:
                return 1
            return 0
        sons.sort(_sort)

        res = []
        if name != '':
            res.append({'type': 'new_tree', 'name': name})
        for p in packs:
            res.append({'type': 'pack', 'pack': p})

        for s in sons:
            r = self._get_pack_tree(s)
            res.extend(r)
        if name != '':
            res.append({'type': 'end_tree', 'name': name})
        print "RETURN PARTIAL", res
        return res

    # We got a pack name, we look for all objects, and search where this
    # host template name is used
    def related_to_pack(self, pack):
        name = pack.get_name().strip()
        print "TRY TO MATCH PACK", name

        res = []
        for tname in pack.templates:
            print "Try to find a sub template of a pack", tname
            tname = tname.strip()
            # First try to match the host template
            tpl = None
            for h in self.get_hosts():
                print "Try to match pack with", h, name, h.get('register', '1') == '0', h.get('name', '') == name
                if h.get('register', '1') == '0' and h.get('name', '') == tname:
                    print "MATCH FOUND for", tname
                    tpl = h
                    break
            print "And now the services of this pack template", tname
            services = []
            for s in self.get_services():
                # I want only the templates
                if s.get('register', '1') != '0':
                    continue
                use = s.get('host_name', '')
                elts = use.split(',')
                elts = [e.strip() for e in elts]
                if tname in elts:
                    print "FOUND A SERVICE THAT MA5TCH", s.get('service_description', '')
                    services.append(s)
            res.append((tpl, services))

        return res

datamgr = DataManagerSKonf()
