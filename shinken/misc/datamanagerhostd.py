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
from shinken.misc.datamanagerskonf import DataManagerSKonf


class FakeRegenerator(object):
    def __init__(self):
        return


class DataManagerHostd(DataManagerSKonf):
    def get_generics(self, table, key):
        r = []
        for i in self.get_all_in_db(table):
            r.append(i)
        return r

    def get_packs(self):
        return self.get_generics('packs', 'pack_name')

    # Get a specific object
    def get_pack(self, pname):
        r = self.get_in_db('packs', 'pack_name', pname)
        return r

    def get_pack_by_id(self, pid):
        r = self.get_in_db('packs', '_id', pid)
        return r

    def get_pack_by_user_packname(self, username, packname):
        value = '%s-%s' % (username, packname)
        r = self.get_in_db('packs', 'link_id', value)
        return r

    def build_pack_tree(self, packs):

        # dirname sons packs
        t = ('', [], [])
        for p in packs:
            path = p.get('path', '/')
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

    def get_pack_tree(self):
        packs = self.get_packs()
        packs = [p for p in packs if p['state'] in ['ok', 'pending']]
        print "GOT IN DB PACKS", packs
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
        name = pack.get('pack_name', 'unknown').strip()
        print "TRY TO MATCH PACK", name

        res = []
        for tname in pack.get('templates', []):
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
            if not tpl:
                continue
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

datamgr = DataManagerHostd()
