#!/usr/bin/env python
#Copyright (C) 2009-2011 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Andreas Karfusehr, andreas@karfusehr.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

from shinken.webui.bottle import redirect
from shinken.misc.filter  import only_related_to
from shinken.misc.sorter import hst_srv_sort

### Will be populated by the UI with it's own value
app = None

import re

# Our page
def get_page(show='all'):
    
    # First we look for the user sid
    # so we bail out if it's a false one
#    sid = app.request.get_cookie("sid")
    

    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
#        return {'app' : app, 'pbs' : [], 'valid_user' : False, 'user' : None, 'navi' : None}
 
    #We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '30'))

    search = app.request.GET.get('search', '')

    pbs = app.datamgr.get_all_problems(to_sort=False)
    
    # Filter with the user interests
    pbs = only_related_to(pbs, user)

    # Sort it now
    pbs.sort(hst_srv_sort)

    # Ok, if need, appli the search filter
    if search:
        print "SEARCHING FOR", search
        print "Before filtering", len(pbs)
        # We compile the patern
        pat = re.compile(search, re.IGNORECASE)
        new_pbs = []
        for p in pbs:
            if pat.search(p.get_full_name()):
                new_pbs.append(p)
                continue
            to_add = False
            for imp in p.impacts:
                if pat.search(imp.get_full_name()):
                    to_add = True
            for src in p.source_problems:
                if pat.search(src.get_full_name()):
                    to_add = True
            if to_add:
                new_pbs.append(p)

        pbs = new_pbs
        print "After filtering", len(pbs)

    total = len(pbs)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = 30
    navi = app.helper.get_navi(total, start, step=30)
    pbs = pbs[start:end]

#    print "get all problems:", pbs
#    for pb in pbs :
#        print pb.get_name()
    return {'app' : app, 'pbs' : pbs, 'valid_user' : True, 'user' : user, 'navi' : navi, 'search' : search, 'page' : 'problems', 'show' : show}



# Our page
def get_all(show='all'):
    
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")
 
    #We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '30'))

    search = app.request.GET.get('search', '')

    all = app.datamgr.get_all_hosts_and_services()

    # Filter or not filter? That is the question....
    #all = only_related_to(all, user)
    
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

    return {'app' : app, 'pbs' : all, 'valid_user' : True, 'user' : user, 'navi' : navi, 'search' : search, 'page' : 'all', 'show' : show}



pages = {get_page : { 'routes' : ['/problems', '/problems/:show'], 'view' : 'problems', 'static' : True},
         get_all : { 'routes' : ['/all', '/all/:show'], 'view' : 'problems', 'static' : True},
         }

