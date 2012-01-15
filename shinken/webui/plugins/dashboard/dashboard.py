#!/usr/bin/env python
# Copyright (C) 2009-2012 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Andreas Karfusehr, andreas@karfusehr.de
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

from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None

# Our page
def get_page():
    
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
    
    schedulers = app.datamgr.get_schedulers()
    brokers = app.datamgr.get_brokers()
    reactionners = app.datamgr.get_reactionners()
    receivers = app.datamgr.get_receivers()
    pollers = app.datamgr.get_pollers()

    return {'app' : app, 'user' : user, 'schedulers' : schedulers,
            'brokers' : brokers, 'reactionners' : reactionners,
            'receivers' : receivers, 'pollers' : pollers,
            }

# Our page
def get_all():
    
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")
 
    #We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '30'))

    search = app.request.GET.get('search', '')

    all = app.datamgr.get_all_hosts_and_services()

    # Ok, if need, appli the search filter
    if search:
        print "SEARCHING FOR", search
        print "Before filtering", len(all)
        # We compile the patern
        pat = re.compile(search, re.IGNORECASE)
        new_all = []
        for p in all:
            if pat.search(p.get_full_name()):
                new_all.append(p)
                continue
            to_add = False
            for imp in p.impacts:
                if pat.search(imp.get_full_name()):
                    to_add = True
            for src in p.source_problems:
                if pat.search(src.get_full_name()):
                    to_add = True
            if to_add:
                new_all.append(p)

        all = new_all
        print "After filtering", len(all)

    total = len(all)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = 30
    navi = app.helper.get_navi(total, start, step=30)
    all = all[start:end]

    return {'app' : app, 'pbs' : all, 'valid_user' : True, 'user' : user, 'navi' : navi, 'search' : search, 'page' : 'all'}



pages = {get_page : { 'routes' : ['/dashboard'], 'view' : 'dashboard', 'static' : True},
         get_all : { 'routes' : ['/dashboard/fullscreen'], 'view' : 'fullscreen', 'static' : True},
         }

