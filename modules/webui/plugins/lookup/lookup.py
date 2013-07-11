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

from shinken.misc.filter  import only_related_to

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


def lookup(name=''):
    app.response.content_type = 'application/json'

    user = app.get_user_auth()
    if not user:
        return []

    if len(name) < 3:
        print "Lookup %s too short, bail out" % name
        return []

    filtered_hosts = only_related_to(app.datamgr.get_hosts(), user)
    hnames = (h.host_name for h in filtered_hosts)
    r = [n for n in hnames if n.startswith(name)]

    return json.dumps(r)


def lookup_post():
    app.response.content_type = 'application/json'

    user = app.get_user_auth()
    if not user:
        return []

    name = app.request.forms.get('value')
    if not name or len(name) < 3:
        print "Lookup POST %s too short, bail out" % name
        return []

    filtered_hosts = only_related_to(app.datamgr.get_hosts(), user)
    hnames = (h.host_name for h in filtered_hosts)
    r = [n for n in hnames if n.startswith(name)]

    return json.dumps(r)

pages = {lookup: {'routes': ['/lookup/:name']},
         lookup_post: {'routes': ['/lookup'], 'method': 'POST'}
         }
