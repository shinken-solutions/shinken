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


# Our page
def get_page():

    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/user/login")

    has_user_pref_mod = app.has_user_preference_module()

    # Look for the widgets as the json entry
    s = app.get_user_preference(user, 'widgets')
    print "Loaded widgets", s, type(s)
    # If void, create an empty one
    if not s:
        app.set_user_preference(user, 'widgets', '[]')
        s = '[]'
    widget_names = json.loads(s)
    print "And now objects", widget_names
    widgets = []

    for w in widget_names:
        if not 'id' in w or not 'position' in w:
            continue

        # by default the widget is for /dashboard
        w['for'] = w.get('for', 'dashboard')
        if not w['for'] == 'dashboard':
            # Not a dashboard widget? I don't want it so
            continue

        i = w['id']
        pos = w['position']
        options = w.get('options', {})
        collapsed = w.get('collapsed', '0')

        ## Try to get the options for this widget
        #option_s = app.get_user_preference(user, 'widget_widget_system_1333371012', default='{}')
        #print "And load options_s", option_s
        #if option_s:
        #    json.loads(option_s)
        #print "And dump options for this widget", options
        w['options'] = json.dumps(options)
        args = {'wid': i, 'collapsed': collapsed}
        args.update(options)
        w['options_uri'] = '&'.join('%s=%s' % (k, v) for (k, v) in args.iteritems())
        widgets.append(w)

    print "Give widgets", widgets
    return {'app': app, 'user': user, 'widgets': widgets, 'has_user_pref_mod' : has_user_pref_mod}

def get_currently():
    
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/user/login")
        return


    return {'app': app, 'user': user}

pages = {get_page: {'routes': ['/dashboard'], 'view': 'dashboard', 'static': True},
         get_currently: { 'routes': ['/dashboard/currently'], 'view': 'currently', 'static': True},
         }
