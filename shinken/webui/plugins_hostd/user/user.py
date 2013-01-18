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

import hashlib
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

from shinken.webui.bottle import redirect, abort

### Will be populated by the UI with it's own value
app = None


# Our page. If the user call /dummy/TOTO arg1 will be TOTO.
# if it's /dummy/, it will be 'nothing'
def get_page(username):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    #uname = user.get('username')
    view_user = app.get_user_by_name(username)
    cur = app.db.packs.find({'user': username, 'state': 'ok'})
    validated_packs = [p for p in cur]

    # Only show pending and refused packs if YOU are the user
    pending_packs = []
    refused_packs = []
    if user == view_user:
        cur = app.db.packs.find({'user': username, 'state': 'pending'})
        pending_packs = [p for p in cur]

        cur = app.db.packs.find({'user': username, 'state': 'refused'})
        refused_packs = [p for p in cur]

    return {'app': app, 'user': user, 'view_user': view_user, 'validated_packs': validated_packs, 'pending_packs': pending_packs,
            'refused_packs': refused_packs}


def post_user():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    # Take the user that send the post and not the
    # form value for security reason of course :)
    username = user.get('username')
    email = app.request.forms.get('email')
    password = app.request.forms.get('password')
    password2 = app.request.forms.get('password2')
    password_hash = None
    if password:
        password_hash = hashlib.sha512(password).hexdigest()
    if password != password2:
        abort(400, 'Wrong password')

    print "Get a user %s update with email %s and hash %s" % (username, email, password_hash)

    app.update_user(username, password_hash, email)
    return


def check_key(api_key):
    user = app.get_user_by_key(api_key)
    app.response.content_type = 'application/json'
    if not user:
        r = {'state': 401, 'text': 'Sorry this key is invalid!'}
        return json.dumps(r)
    r = {'state': 200, 'text': 'Congrats! Connexion is OK!'}
    return json.dumps(r)

pages = {get_page: {'routes': ['/user/:username'], 'view': 'user', 'static': True},
         post_user: {'routes': ['/user'], 'method': 'POST', 'view': 'user', 'static': True},
         check_key: {'routes': ['/checkkey/:api_key']},
         }
