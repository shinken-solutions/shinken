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


# Our page
def get_graphs_widget():

    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    search = app.request.GET.get('search', '')

    if not search:
        search = 'localhost'

    # Look for an host or a service?
    elt = None
    if not '/' in search:
        elt = app.datamgr.get_host(search)
    else:
        parts = search.split('/', 1)
        elt = app.datamgr.get_service(parts[0], parts[1])

    wid = app.request.GET.get('wid', 'widget_graphs_' + str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')

    options = {'search': {'value': search, 'type': 'hst_srv', 'label': 'Element name'},}

    title = 'Element graphs for %s' % search

    return {'app': app, 'elt': elt, 'user': user,
            'wid': wid, 'collapsed': collapsed, 'options': options, 'base_url': '/widget/graphs', 'title': title,
            }

widget_desc = '''<h3>Graphs</h3>
Show the perfdata graph
'''

pages = {
    get_graphs_widget: {'routes': ['/widget/graphs'], 'view': 'widget_graphs', 'static': True, 'widget': ['dashboard'], 'widget_desc': widget_desc, 'widget_name': 'graphs', 'widget_picture': '/static/graphs/img/widget_graphs.png'},
    }
