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

import json
import hashlib

from shinken.webui.bottle import redirect, abort

### Will be populated by the UI with it's own value
app = None


# Our page. If the useer call /dummy/TOTO arg1 will be TOTO.
# if it's /dummy/, it will be 'nothing'
def register():
    error = app.request.GET.get('error', '')
    success = app.request.GET.get('success', '')
    return {'app': app, 'user': {}, 'error': error, 'success': success}


def do_register():
    username = app.request.forms.get('username')
    email = app.request.forms.get('email')
    password = app.request.forms.get('password')
    password_hash = hashlib.sha512(password).hexdigest()
    cli_mode = app.request.forms.get('cli_mode', '0')

    print "Get a new user %s with email %s and hash %s" % (username, email, password_hash)
    if not app.is_name_available(username):
        if cli_mode == '1':
            app.response.content_type = 'application/json'
            return json.dumps({'state': 400, 'text': 'Sorry, this username is not available'})
        redirect('/register?error=Sorry, this username is not available')

    app.register_user(username, password_hash, email)
    if cli_mode == '1':
        app.response.content_type = 'application/json'
        return json.dumps({'state': 200, 'text': 'Registering success, please look at your email and click in the link in it to validate your account'})
    redirect('/register?success=Registering success, please look at your email and click in the link in it to validate your account')


def validate():
    activating_key = app.request.GET.get('activating_key', '')
    activated = False
    if activating_key:
        activated = app.validate_user(activating_key)
    return {'app': app, 'user': {}, 'activating_key': activating_key, 'activated': activated}


def is_name_available():
    app.response.content_type = 'application/json'

    name = app.request.forms.get('value')
    if not name or len(name) < 3:
        print "Lookup POST %s too short, bail out" % name
        return json.dumps('')

    print "Lookup for", name, "in users"
    b = app.is_name_available(name)
    print "Return", b
    return json.dumps(b)


def get_api_key():
    app.response.content_type = 'application/json'
    login = app.request.forms.get('login', '')
    password = app.request.forms.get('password', '')
    is_auth = app.check_auth(login, password)
    is_activated = app.is_actitaved(login)
    if not is_activated:
        abort(400, 'Sorry your account is not wet validated, please look at your emails!')

    if is_auth:
        key = app.get_api_key(login)
        if key:
            r = {'api_key': key}
            return json.dumps(r)
        else:
            abort(400, 'Sorry, there is a problem with your api key.')
    else:
        abort(401, 'Sorry, you need valid credentials to access to your API key')

pages = {register: {'routes': ['/register'], 'view': 'register', 'static': True},
         is_name_available: {'routes': ['/availability'], 'method': 'POST', 'view': None, 'static': True},
         do_register: {'routes': ['/register'], 'method': 'POST', 'view': 'register', 'static': True},
         validate: {'routes': ['/validate'], 'view': 'validate', 'static': True},
         get_api_key: {'routes': ['/apikey'], 'method': 'POST'},
         }
