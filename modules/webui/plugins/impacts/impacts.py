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

from shinken.util import safe_print
from shinken.misc.filter  import only_related_to

# Global value that will be changed by the main app
app = None


# Sort hosts and services by impact, states and co
def hst_srv_sort(s1, s2):
    if s1.business_impact > s2.business_impact:
        return -1
    if s2.business_impact > s1.business_impact:
        return 1
    # ok, here, same business_impact
    # Compare warn and crit state
    if s1.state_id > s2.state_id:
        return -1
    if s2.state_id > s1.state_id:
        return 1
    # Ok, so by name...
    return s1.get_full_name() > s2.get_full_name()


def show_impacts():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/user/login")
        #return {'app': app, 'impacts': {}, 'valid_user': False, 'user': user}

    all_imp_impacts = only_related_to(app.datamgr.get_important_elements(),user)
    all_imp_impacts.sort(hst_srv_sort)

    impacts = {}

    imp_id = 0
    for imp in all_imp_impacts:
        #safe_print("FIND A BAD SERVICE IN IMPACTS", imp.get_dbg_name())
        imp_id += 1
        impacts[imp_id] = imp

    return {'app': app, 'impacts': impacts, 'valid_user': True, 'user': user}


def impacts_widget():
    d = show_impacts()

    wid = app.request.GET.get('wid', 'widget_impacts_' + str(int(time.time())))
    collapsed = (app.request.GET.get('collapsed', 'False') == 'True')

    nb_elements = max(1, int(app.request.GET.get('nb_elements', '5')))
    # Now filter for the good number of impacts to show
    new_impacts = {}
    for (k, v) in d['impacts'].iteritems():
        if k <= nb_elements:
            new_impacts[k] = v
    d['impacts'] = new_impacts

    options = {'nb_elements': {'value': nb_elements, 'type': 'int', 'label': 'Max number of elements to show'},
               }

    d.update({'wid': wid, 'collapsed': collapsed, 'options': options,
            'base_url': '/widget/impacts', 'title': 'Impacts'})

    return d

widget_desc = '<h4>Impacts</h3>Show an aggregated view of the most business impacts!</h4>'

pages = {show_impacts: {'routes': ['/impacts'], 'view': 'impacts', 'static': True},
         impacts_widget: {'routes': ['/widget/impacts'], 'view': 'widget_impacts', 'static': True, 'widget': ['dashboard'], 'widget_desc': widget_desc, 'widget_name': 'impacts', 'widget_picture': '/static/impacts/img/widget_impacts.png'},
         }
