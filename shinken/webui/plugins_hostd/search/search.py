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

def search_post():
    app.response.content_type = 'application/json'

    search = app.request.forms.get('search')
    if not search or len(search) < 3:
        print "Lookup POST %s too short, bail out" % search
        return []

    print "Lookup for", search, "in pack"
    # TODO : less PERFORMANCE KILLER QUERY!
    packs = app.datamgr.get_packs()
    res = []
    for p in packs:
        if p.get('state') not in ['ok', 'pending']:
            continue
        if search in p['pack_name'] or search in p.get('description', ''):
            print "MATCH THE PACK", p
            d = {}
            d['_id'] = p['_id']
            d['user'] = p['user']
            d['pack_name'] = p['pack_name']
            d['description'] = p.get('description', '')
            d['templates'] = p.get('templates', [])
            # TODO : manage a real server?
            d['img'] = 'http://%s:7765/static/%s/images/sets/%s/tag.png' % (SRV, p['_id'], d['pack_name'])
            d['install'] = 'http://%s:7765/getpack/%s' % (SRV, p['_id'])
            res.append(d)
    return json.dumps(res)



pages = {search_post : { 'routes' : ['/search'] , 'method' : 'POST'},
         }

