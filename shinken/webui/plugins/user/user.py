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

from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None


def save_pref():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    key = app.request.forms.get('key', None)
    value = app.request.forms.get('value', None)

    if key is None or value is None:
        return

    s = json.dumps('{%s: %s}' % (key, value))

    print "We will save for the user", user.get_name(), key, ':', value
    print "As %s" % s

    app.set_user_preference(user, key, value)

    return

def save_common_pref():
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    key = app.request.forms.get('key', None)
    value = app.request.forms.get('value', None)

    if key is None or value is None:
        return

    s = json.dumps('{%s: %s}' % (key, value))

    print "We will save common pref ", key, ':', value
    print "As %s" % s

    if user.is_admin:
        app.set_common_preference( key, value)

    return


pages = {save_pref: {'routes': ['/user/save_pref'], 'method': 'POST'}, save_common_pref: {'routes': ['/user/save_common_pref'], 'method': 'POST'}}

