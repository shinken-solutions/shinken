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

### Will be populated by the UI with it's own value
app = None

try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error : you need the json or simplejson module"
        raise


# HACK
import socket
SRV = socket.gethostname()

def give_pack(p):
    d = {}
    d['_id'] = p['_id']
    d['user'] = p['user']
    d['pack_name'] = p['pack_name']
    d['description'] = p.get('description', '')
    d['templates'] = p.get('templates', [])
    # TODO : manage a real server?
    d['img'] = 'http://%s:7765/static/%s/images/sets/%s/tag.png' % (SRV, p['_id'], d['pack_name'])
    d['install'] = 'http://%s:7765/getpack/%s' % (SRV, p['_id'])
    return d


def search_post():
    app.response.content_type = 'application/json'

    search = app.request.forms.get('search')

    if not search  or len(search) < 2 :
        print "Lookup POST %s too short or missing filter, I bail out" % search
        return json.dumps([])


    print "Lookup for", search, "in pack"
    # TODO : less PERFORMANCE KILLER QUERY!
    packs = app.datamgr.get_packs()
    res = []
    for p in packs:
        if p.get('state') not in ['ok', 'pending']:
            continue
        
        if search and search in p['pack_name'] or search in p.get('description', ''):
            d = give_pack(p)
            res.append(d)
            continue

        if search:
            cats = p.get('path', '').split('/')
            if search in cats:
                d = give_pack(p)
                res.append(d)
            continue
        
    return json.dumps(res)




def search_categories():
    app.response.content_type = 'application/json'

    root = app.request.forms.get('root')

    if not root:
        print "Lookup categories but missing root!"
        return json.dumps([])


    print "Lookup for categories from root", root, "in pack"

    # TODO : less PERFORMANCE KILLER QUERY!
    packs = app.datamgr.get_packs()
    tree = {'name' : '/', 'nb' : 0, 'sons' : {}}
    for p in packs:
        if p.get('state') not in ['ok', 'pending']:
            continue
        
        cats = p.get('path', '').split('/')
        cats = [c for c in cats if c != '']
        pos = tree
        name = ''
        for cat in cats:
            name += '/'+cat
            print "Doing cat", cat
            # If not already declared, add my node
            if cat not in pos['sons']:
                pos['sons'][cat] = {'name' : name, 'nb' : 0, 'sons' : {}}
            pos['sons'][cat]['nb'] += 1
            # Now go deeper in the tree :)
            print "Were I came from", pos
            pos = pos['sons'][cat]
            print "My new pos", pos
        
    print "Tree", tree
        
    return json.dumps(tree)



pages = {search_post : { 'routes' : ['/search'] , 'method' : 'POST'},
         search_categories : { 'routes' : ['/categories'] , 'method' : 'POST'},
         }

