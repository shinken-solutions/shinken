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

from shinken.webui.bottle import redirect, abort

### Will be populated by the UI with it's own value
app = None


def add_pack_page():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    return {'app': app, 'user': user}


def push_new_pack():

    print "FUCK", app.request.forms.__dict__
    key = app.request.forms.get('key')
    data = app.request.files.get('data')
    print "KEY", key
    print "DATA", data.file
    if not key:
        print "NOT KEY"
    if not data.file:
        print "NO FILE"

    is_cli = True
    # Maybe it's with a cookie based auth
    user = app.get_user_auth()
    if not user:
        # Check if the user is validated
        user = app.get_user_by_key(key)
    else:
        is_cli = False
        # Get the user key :)
        key = user['api_key']

    if not user:
        print "Sorry, you give a wrong APIKEY or your account i"
        if is_cli:
            abort(400, 'Sorry, you give a wrong APIKEY or your account is not validated')
        else:
            app.response.content_type = 'application/json'
            return json.dumps("Sorry, you give a wrong APIKEY or your account is not validated")


    if key and data.file:
        print "READING A FILE"
        # LIMIT AT 5MB
        raw = data.file.read(5000000)
        over = data.file.read(1)
        filename = data.filename
        if over:
            if is_cli:
                abort(400, 'Sorry your file is too big!')
            else:
                app.response.content_type = 'application/json'
                return json.dumps({'state': 'error', 'text': 'Sorry your file is too big!'})
        uname = user.get('username')
        app.save_new_pack(uname, filename, raw)
        if is_cli:
            return "Hello %s! You uploaded %s (%d bytes)." % (uname, filename, len(raw))
        else:
            app.response.content_type = 'application/json'
            return json.dumps({'state': 'ok', 'text': "Hello %s! You uploaded %s (%d bytes)." % (key, filename, len(raw))})
    print "You missed a field."
    if is_cli:
        abort(400, 'You missed a field.')
    else:
        app.response.content_type = 'application/json'
        return json.dumps({'state': 'error', 'text': 'Sorry you missed a filed'})


def push_stats():
    print "FUCK", app.request.forms.__dict__
    key = app.request.forms.get('key')
    data = app.request.files.get('data')
    print "KEY", key
    print "DATA", data.file
    if not key:
        print "NOT KEY"
    if not data.file:
        print "NO FILE"

    is_cli = True
    # Maybe it's with a cookie based auth
    user = app.get_user_auth()
    if not user:
        # Check if the user is validated
        user = app.get_user_by_key(key)
    else:
        is_cli = False
        # Get the user key :)
        key = user['api_key']

    if not user:
        print "Sorry, you give a wrong APIKEY or your account i"
        if is_cli:
            abort(400, 'Sorry, you give a wrong APIKEY or your account is not validated')
        else:
            app.response.content_type = 'application/json'
            return json.dumps("Sorry, you give a wrong APIKEY or your account is not validated")


    if key and data.file:
        print "READING A stats FILE"
        # LIMIT AT 5MB
        raw = data.file.read(5000000)
        over = data.file.read(1)
        filename = data.filename
        if over:
            if is_cli:
                abort(400, 'Sorry your file is too big!')
            else:
                app.response.content_type = 'application/json'
                return json.dumps({'state': 'error', 'text': 'Sorry your file is too big!'})
        uname = user.get('username')
        stats = json.loads(raw)
        print "WE READ A STATS DATA for user", user, "STATS:", stats
        app.save_user_stats(user, stats)
        if is_cli:
            return "Hello %s! You uploaded %s (%d bytes)." % (uname, filename, len(raw))
        else:
            app.response.content_type = 'application/json'
            return json.dumps({'state': 'ok', 'text': "Hello %s! You uploaded %s (%d bytes)." % (key, filename, len(raw))})
    print "You missed a field."
    if is_cli:
        abort(400, 'You missed a field.')
    else:
        app.response.content_type = 'application/json'
        return json.dumps({'state': 'error', 'text': 'Sorry you missed a filed'})

pages = {push_new_pack: {'routes': ['/pushpack'], 'method': 'POST', 'view': None, 'static': True},
         push_stats: {'routes': ['/pushstats'], 'method': 'POST', 'view': None, 'static': True},

         add_pack_page: {'routes': ['/addpack'], 'view': 'addpack', 'static': True},
         }
