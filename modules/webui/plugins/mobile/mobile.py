#!/usr/bin/env python
# Copyright (C) 2009-2011:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#    Andreas Karfusehr, andreas@karfusehr.de
#    Mael Vincent, mael.vincent0@gmail.com
#    Damien Mathieu, damien.mth@gmail.com
#    Hugo Viricel, hugo.viricel@gmail.com
#    Valentin Brajon, vbrajon@gmail.com
#    Julien Pilou, pilou.julien@gmail.com
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
from shinken.util import safe_print
from helper import hst_srv_sort
from shinken.misc.sorter import worse_first

try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error: you need the json or simplejson module"
        raise

### Will be populated by the UI with it's own value
app = None


def main():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")
        return

    all_imp_impacts = app.datamgr.get_important_elements()

    all_pbs = app.datamgr.get_all_problems()

    return {'app': app, 'user': user, 'impacts': all_imp_impacts, 'problems': all_pbs}


def impacts():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")
        return

    # We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '5'))

    all_imp_impacts = app.datamgr.get_important_elements()
    all_imp_impacts.sort(worse_first)

    total = len(all_imp_impacts)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = 5

    navi = app.helper.get_navi(total, start, step=5)
    all_imp_impacts = all_imp_impacts[start:end]

    return {'app': app, 'user': user, 'navi': navi, 'impacts': all_imp_impacts}


def problems():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")
        return

    # We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '5'))

    all_pbs = app.datamgr.get_all_problems()

    # Now sort it!
    all_pbs.sort(hst_srv_sort)

    total = len(all_pbs)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = 5

    navi = app.helper.get_navi(total, start, step=5)
    all_pbs = all_pbs[start:end]

    return {'app': app, 'user': user, 'navi': navi, 'problems': all_pbs, 'menu_part': '/problems'}


def dashboard():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")
        return

    # We want to limit the number of elements
    start = int(app.request.GET.get('start', '0'))
    end = int(app.request.GET.get('end', '5'))

    all_pbs = app.datamgr.get_all_hosts_and_services()

    # Now sort it!
    all_pbs.sort(hst_srv_sort)

    total = len(all_pbs)
    # If we overflow, came back as normal
    if start > total:
        start = 0
        end = 5

    navi = app.helper.get_navi(total, start, step=5)
    all_pbs = all_pbs[start:end]

    return {'app': app, 'user': user, 'navi': navi, 'problems': all_pbs, 'menu_part': '/dashboard'}


def system_page():
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")

    schedulers = app.datamgr.get_schedulers()
    brokers = app.datamgr.get_brokers()
    reactionners = app.datamgr.get_reactionners()
    receivers = app.datamgr.get_receivers()
    pollers = app.datamgr.get_pollers()

    return {'app': app, 'user': user, 'schedulers': schedulers,
            'brokers': brokers, 'reactionners': reactionners,
            'receivers': receivers, 'pollers': pollers,
            }


def show_log():
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")

    schedulers = app.datamgr.get_schedulers()
    brokers = app.datamgr.get_brokers()
    reactionners = app.datamgr.get_reactionners()
    receivers = app.datamgr.get_receivers()
    pollers = app.datamgr.get_pollers()

    return {'app': app, 'user': user, 'schedulers': schedulers,
            'brokers': brokers, 'reactionners': reactionners,
            'receivers': receivers, 'pollers': pollers,
            }


# Main impacts view
#@route('/host')
def show_host(name):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")

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
        app.bottle.redirect("/mobile/")
#        return {'app': app, 'elt': None, 'valid_user': False, 'user': user}


    # Ok we are in a detail page but the user ask for a specific search
    search = app.request.GET.get('global_search', None)
    if search:
        new_h = app.datamgr.get_host(search)
        if new_h:
            app.bottle.redirect("/mobile/host/" + search)

    # Get graph data. By default, show last 4 hours
    now = int(time.time())
    graphstart = int(app.request.GET.get('graphstart', str(now - 4*3600)))
    graphend = int(app.request.GET.get('graphend', str(now)))

    # Ok, we can lookup it :)
    s = app.datamgr.get_service(hname, desc)
    return {'app': app, 'elt': s, 'valid_user': True, 'user': user, 'graphstart': graphstart,
            'graphend': graphend}


# The wall
# Sort hosts and services by impact, states and co
def sort_by_last_state_change(s1, s2):
    if s1.last_state_change > s2.last_state_change:
        return -1
    else:
        return 1


# Get the div for each element
def get_div(elt):
    icon = app.helper.get_icon_state(elt)
    stars = ''
    for i in range(2, elt.business_impact):
        stars += '''<div class="criticity-inpb-icon-%d">
                  <img src="/static/images/star.png">
              </div>''' % (i-1)
    lnk = app.helper.get_link_dest(elt)
    button = app.helper.get_button('', img='/static/images/search.png')
    pulse = ''
    if elt.is_problem or (elt.state_id != 0 and elt.business_impact > 2):
        pulse = '<span class="wall-pulse pulse" title=""></span>'
    s = """
        %s
          %s
        <div class="item-icon">
          <img class="wall-icon" src="%s"></img>
        </div>
        <div class="item-text">
          <span class="state_%s">%s <br/> %s</span>
        </div>
        <div class="item-button">
        <a href="%s">%s</a>
        </div>

        """ % (stars, pulse, icon, elt.state.lower(), elt.state, elt.get_full_name(), lnk, button)# stars, button)
    s = s.encode('utf8', 'ignore')
    return s


def wall():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/mobile/")

    all_imp_impacts = app.datamgr.get_important_elements()
    all_imp_impacts.sort(hst_srv_sort)

    impacts = all_imp_impacts
    all_pbs = app.datamgr.get_all_problems()
    now = time.time()
    # Get only the last 10min errors
    all_pbs = [pb for pb in all_pbs if pb.last_state_change > now - 600]
    # And sort it
    all_pbs.sort(hst_srv_sort)  # sort_by_last_state_change)

    return {'app': app, 'user': user, 'impacts': impacts, 'problems': all_pbs}

pages = {main: {'routes': ['/mobile/main'], 'view': 'mobile_main', 'static': True},
         impacts: {'routes': ['/mobile/impacts'], 'view': 'mobile_impacts', 'static': True},
         problems: {'routes': ['/mobile/problems'], 'view': 'mobile_problems', 'static': True},
         dashboard: {'routes': ['/mobile/dashboard'], 'view': 'mobile_problems', 'static': True},
         system_page: {'routes': ['/mobile/system'], 'view': 'mobile_system', 'static': True},
         show_log: {'routes': ['/mobile/log'], 'view': 'mobile_log', 'static': True},
         show_host: {'routes': ['/mobile/host/:name'], 'view': 'mobile_eltdetail', 'static': True},
         show_service: {'routes': ['/mobile/service/:hname/:desc#.+#'], 'view': 'mobile_eltdetail', 'static': True},
         wall: {'routes': ['/mobile/wall/', '/mobile/wall'], 'view': 'mobile_wall', 'static': True},
         }
