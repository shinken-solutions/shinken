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


def lookup(cls='', name=''):
    app.response.content_type = 'application/json'

    user = app.get_user_auth()
    if not user:
        return []

    sources = {'host': app.host_templates, 'service': app.service_templates,
               'contact': app.contact_templates, 'timeperiod': app.timeperiod_templates}

    # Look for a valid source
    if cls not in sources:
        print "Lookup: bad class", cls
        return []

    # And a name not too short
    if len(name) < 3:
        print "Lookup %s too short, bail out" % name
        return []

    print "Lookup for", name, "in", cls
    tags = set()
    for h in sources[cls].values():
        print "Template", h
        if hasattr(h, 'name'):
            tags.add(h.name)
    r = [n for n in tags if n.startswith(name)]

    print "RES", r

    return json.dumps(r)


def lookup_tag_post(cls=''):
    app.response.content_type = 'application/json'

    ## user = app.get_user_auth()
    ## if not user:
    ##     return []
    sources = {'host': app.host_templates, 'service': app.service_templates,
               'contact': app.contact_templates, 'timeperiod': app.timeperiod_templates}


    if cls not in sources:
        print "Lookup: bad class", cls
        return []

    name = app.request.forms.get('value')
    if not name or len(name) < 3:
        print "Lookup POST %s too short, bail out" % name
        return []

    print "Lookup for", name, "in", sources[cls]
    tags = set()
    for h in sources[cls].values():
        print "Template", h
        if hasattr(h, 'name'):
            tags.add(h.name)
    r = [{'id': n, 'name': n} for n in tags if n.startswith(name)]

    print "RES", r

    return json.dumps(r)

pages = {lookup_tag_post: {'routes': ['/lookup/:cls/tag'], 'method': 'POST'},
         lookup: {'routes': ['/lookup/:cls/tag/:name']},
         }
