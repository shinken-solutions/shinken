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

import time
import re

# Our page
def get_page():

    return get_view('problems')
    
    # First we look for the user sid
    # so we bail out if it's a false one
#    sid = app.request.get_cookie("sid")
    

    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
#        return {'app' : app, 'pbs' : [], 'valid_user' : False, 'user' : None, 'navi' : None}

    print 'DUMP GET', app.request.GET.__dict__
 
    #We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '30'))


    # We will keep a trace of our filters
    filters = {}

    search = app.request.GET.get('search', '')
    if search == '':
        search = app.request.GET.get('global_search', '')

    pbs = app.datamgr.get_all_problems(to_sort=False)
    
    # Filter with the user interests
    pbs = only_related_to(pbs, user)
    
    filter_hg = app.get_user_preference(user, 'filter_hg', '')
    filters['filter_hg'] = filter_hg
    print 'HG name filter : ', filter_hg

    if filter_hg:
        print 'WE GOT A FILTER', filter_hg
        hg = app.datamgr.get_hostgroup(filter_hg)
        if hg:            
            print 'And a valid hg filtering'
            pbs = [pb for pb in pbs if hg in pb.get_hostgroups()]

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

    # Now sort it!
    pbs.sort(hst_srv_sort)


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
    return {'app' : app, 'pbs' : pbs, 'valid_user' : True, 'user' : user, 'navi' : navi, 'search' : search, 'page' : 'problems', 'filters' : filters}



# Our page
def get_all():

    return get_view('all')
    
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")
 
    #We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '30'))

    # We keep a trace of our filters
    filters = {'filter_hg' : ''}
    

    search = app.request.GET.get('search', '')
    if search == '':
        search = app.request.GET.get('global_search', '')


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

    return {'app' : app, 'pbs' : all, 'valid_user' : True, 'user' : user, 'navi' : navi, 'search' : search, 'page' : 'all', 'filters' : filters}




# Our View code. We will get different data from all and /problems
# but it's mainly filtering changes
def get_view(page):

    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    print 'DUMP COMMON GET', app.request.GET.__dict__
 
    # We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '30'))

    # We will keep a trace of our filters
    filters = {}
    ts = ['hst_srv', 'hg']
    for t in ts:
        filters[t] = []

    search = app.request.GET.getall('search')
    if search == []:
        search = app.request.GET.get('global_search', '')

    # Most of the case, search will be a simple string, if so
    # make it a list of this string
    if isinstance(search, basestring):
        search = [search]

    search_str = '&'.join(search)
    print 'Search str=', search_str
    print 'And search', search

    items = []
    if page == 'problems':
        items = app.datamgr.get_all_problems(to_sort=False)
    elif page == 'all':
        items = app.datamgr.get_all_hosts_and_services()
    else: #WTF?!?
        redirect("/problems")
    
    # Filter with the user interests
    items = only_related_to(items, user)
    
    # Ok, if need, appli the search filter
    for s in search:
        s = s.strip()
        if not s:
            continue
            
        print "SEARCHING FOR", s
        print "Before filtering", len(items)
        
        elts = s.split(':', 1)
        t = 'hst_srv'
        if len(elts) > 1:
            t = elts[0]
            s = elts[1]
            
        print 'Search for type %s and patern %s' % (t, s)
        if not t in filters:
            filters[t] = []
        filters[t].append(s)

        if t == 'hst_srv':
            # We compile the patern
            pat = re.compile(s, re.IGNORECASE)
            new_items = []
            for i in items:
                if pat.search(i.get_full_name()):
                    new_items.append(i)
                    continue
                to_add = False
                for imp in i.impacts:
                    if pat.search(imp.get_full_name()):
                        to_add = True
                for src in i.source_problems:
                    if pat.search(src.get_full_name()):
                        to_add = True
                if to_add:
                    new_items.append(i)

            items = new_items

        if t == 'hg':
            hg = app.datamgr.get_hostgroup(s)
            print 'And a valid hg filtering for', s
            items = [i for i in items if hg in i.get_hostgroups()]

        print "After filtering for",t, s,'we got', len(items)            
        
    # Now sort it!
    items.sort(hst_srv_sort)

    total = len(items)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = 30

    navi = app.helper.get_navi(total, start, step=30)
    items = items[start:end]

#    print "get all problems:", pbs
#    for pb in pbs :
#        print pb.get_name()
    return {'app' : app, 'pbs' : items, 'user' : user, 'navi' : navi, 'search' : search_str, 'page' : page, 'filters' : filters}




# Our page
def get_pbs_widget():
    
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    # We want to limit the number of elements, The user will be able to increase it
    nb_elements = max(0, int(app.request.GET.get('nb_elements', '10')))
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

        pbs = new_pbs[:nb_elements]
        print "After filtering", len(pbs)

    pbs = pbs[:nb_elements]

    wid = app.request.GET.get('wid', 'widget_problems_'+str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')

    options = {'search' : {'value' : search, 'type' : 'text', 'label' : 'Filter by name'},
               'nb_elements' : {'value' : nb_elements, 'type' : 'int', 'label' : 'Max number of elements to show'},
               }

    title = 'IT problems'
    if search:
        title = 'IT problems (%s)' % search


    return {'app' : app, 'pbs' : pbs, 'user' : user, 'search' : search, 'page' : 'problems',
            'wid' : wid, 'collapsed' : collapsed, 'options' : options, 'base_url' : '/widget/problems', 'title' : title,
            }


widget_desc = '''<h3>IT problems</h3>
Show the most impacting IT problems
'''

pages = {get_page : { 'routes' : ['/problems'], 'view' : 'problems', 'static' : True},
         get_all : { 'routes' : ['/all'], 'view' : 'problems', 'static' : True},
         get_pbs_widget : {'routes' : ['/widget/problems'], 'view' : 'widget_problems', 'static' : True, 'widget' : ['dashboard'], 'widget_desc' : widget_desc, 'widget_name' : 'problems'},
         }

