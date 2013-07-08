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

import time

from shinken.util import safe_print


# Main impacts view
#@route('/host')
def show_host(name):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/user/login")

    # Ok we are in a detail page but the user ask for a specific search
    search = app.request.GET.get('global_search', None)
    if search:
        new_h = app.datamgr.get_host(search)
        if new_h:
            app.bottle.redirect("/host/" + search)

    # Get graph data. By default, show last 4 hours
    now = int(time.time())
    graphstart = int(app.request.GET.get('graphstart', str(now - 4*3600)))
    graphend = int(app.request.GET.get('graphend', str(now)))

    # Ok, we can lookup it
    h = app.datamgr.get_host(name)
    return {'app': app, 'elt': h, 'valid_user': True, 'user': user, 'graphstart': graphstart,
            'graphend': graphend}


def show_service(hname, desc):

    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/user/login")
#        return {'app': app, 'elt': None, 'valid_user': False, 'user': user}


    # Ok we are in a detail page but the user ask for a specific search
    search = app.request.GET.get('global_search', None)
    if search:
        new_h = app.datamgr.get_host(search)
        if new_h:
            app.bottle.redirect("/host/" + search)

    # Get graph data. By default, show last 4 hours
    now = int(time.time())
    graphstart = int(app.request.GET.get('graphstart', str(now - 4*3600)))
    graphend = int(app.request.GET.get('graphend', str(now)))

    # Ok, we can lookup it :)
    s = app.datamgr.get_service(hname, desc)
    return {'app': app, 'elt': s, 'valid_user': True, 'user': user, 'graphstart': graphstart,
            'graphend': graphend}

pages = {show_host: {'routes': ['/host/:name'], 'view': 'eltdetail', 'static': True},
         show_service: {'routes': ['/service/:hname/:desc#.+#'], 'view': 'eltdetail', 'static': True},
         }
