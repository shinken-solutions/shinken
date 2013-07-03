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

from helper import hst_srv_sort
from shinken.util import safe_print
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


# Our page
def get_page():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/user/login")

    all_imp_impacts = app.datamgr.get_important_elements()
    all_imp_impacts.sort(hst_srv_sort)
    #all_imp_impacts.sort(hst_srv_sort)

    #all_imp_impacts = app.datamgr.get_services() #important_elements()

    impacts = all_imp_impacts
    ## for imp in all_imp_impacts:
    ##     safe_print("FIND A BAD SERVICE IN IMPACTS", imp.get_dbg_name())
    ##     d = {'name': imp.get_full_name().encode('utf8', 'ignore'),
    ##          "title": "My Image 3", "thumb": "/static/images/state_flapping.png", "zoom": "/static/images/state_flapping.png",
    ##          "html": get_div(imp)}
    ##     impacts.append(d)

    # Got in json format
    #j_impacts = json.dumps(impacts)
    #print "Return impact in json", j_impacts
    all_pbs = app.datamgr.get_all_problems()
    now = time.time()
    # Get only the last 10min errors
    all_pbs = [pb for pb in all_pbs if pb.last_state_change > now - 600]
    # And sort it
    all_pbs.sort(hst_srv_sort)  # sort_by_last_state_change)

    return {'app': app, 'user': user, 'impacts': impacts, 'problems': all_pbs}

pages = {get_page: {'routes': ['/wall/', '/wall'], 'view': 'wall', 'static': True}}
