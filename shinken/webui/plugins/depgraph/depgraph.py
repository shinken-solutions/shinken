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

import time
from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None


def depgraph_host(name):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'app': app, 'elt': None, 'valid_user': False}

    # Ok we are in a detail page but the user ask for a specific search
    search = app.request.GET.get('global_search', None)
    loop = bool(int(app.request.GET.get('loop', '0')))
    loop_time = int(app.request.GET.get('loop_time', '10'))
    
    if search:
        new_h = app.datamgr.get_host(search)
        if new_h:
            redirect("/depgraph/" + search)

    h = app.datamgr.get_host(name)
    return {'app': app, 'elt': h, 'user': user, 'valid_user': True, 'loop' : loop, 'loop_time' : loop_time}


def depgraph_srv(hname, desc):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'app': app, 'elt': None, 'valid_user': False}

    loop = bool(int(app.request.GET.get('loop', '0')))
    loop_time = int(app.request.GET.get('loop_time', '10'))

    # Ok we are in a detail page but the user ask for a specific search
    search = app.request.GET.get('global_search', None)
    if search:
        new_h = app.datamgr.get_host(search)
        if new_h:
            redirect("/depgraph/" + search)

    s = app.datamgr.get_service(hname, desc)
    return {'app': app, 'elt': s, 'user': user, 'valid_user': True, 'loop' : loop, 'loop_time' : loop_time}


def get_depgraph_widget():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'app': app, 'elt': None, 'valid_user': False}

    search = app.request.GET.get('search', '').strip()

    if not search:
        # Ok look for the first host we can find
        hosts = app.datamgr.get_hosts()
        for h in hosts:
            search = h.get_name()
            break


    elts = search.split('/', 1)
    if len(elts) == 1:
        s = app.datamgr.get_host(search)
    else:  # ok we got a service! :)
        s = app.datamgr.get_service(elts[0], elts[1])

    wid = app.request.GET.get('wid', 'widget_depgraph_' + str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')

    options = {'search': {'value': search, 'type': 'hst_srv', 'label': 'Search an element'},
               }

    title = 'Relation graph for %s' % search

    return {'app': app, 'elt': s, 'user': user,
            'wid': wid, 'collapsed': collapsed, 'options': options, 'base_url': '/widget/depgraph', 'title': title,
            }


def get_depgraph_inner(name):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        return {'app': app, 'elt': None, 'user': None}

    elt = None
    if '/' in name:
        elts = name.split('/', 1)
        elt = app.datamgr.get_service(elts[0], elts[1])
    else:
        elt = app.datamgr.get_host(name)

    return {'app': app, 'elt': elt, 'user': user}

widget_desc = '''<h4>Relation graph</h4>
Show a graph of an object relations
'''

pages = {depgraph_host: {'routes': ['/depgraph/:name'], 'view': 'depgraph', 'static': True},
         depgraph_srv: {'routes': ['/depgraph/:hname/:desc'], 'view': 'depgraph', 'static': True},
         get_depgraph_widget: {'routes': ['/widget/depgraph'], 'view': 'widget_depgraph', 'static': True, 'widget': ['dashboard'], 'widget_desc': widget_desc, 'widget_name': 'depgraph', 'widget_picture': '/static/depgraph/img/widget_depgraph.png'},
         get_depgraph_inner: {'routes': ['/inner/depgraph/:name#.+#'], 'view': 'inner_depgraph', 'static': True},
         }
