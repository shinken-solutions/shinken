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

from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None


# Our page
def get_page():
    return user_login()


def user_login():
    user = app.get_user_auth()
    if user:
        redirect("/problems")

    err = app.request.GET.get('error', None)
    login_text = app.login_text

    return {'error': err, 'login_text': login_text}


def user_login_redirect():
    redirect("/user/login")
    return {}


def user_logout():
    # To delete it, send the same, with different date
    user_name = app.request.get_cookie("user", secret=app.auth_secret)
    if user_name:
        app.response.set_cookie('user', False, secret=app.auth_secret, path='/')
    else:
        app.response.set_cookie('user', '', secret=app.auth_secret, path='/')
    redirect("/user/login")
    return {}


def user_auth():
    print "Got forms"
    login = app.request.forms.get('login', '')
    password = app.request.forms.get('password', '')
    is_mobile = app.request.forms.get('is_mobile', '0')
    is_auth = app.check_auth(login, password)

    if is_auth:
        app.response.set_cookie('user', login, secret=app.auth_secret, path='/', expires='Fri, 01 Jan 2100 00:00:00 GMT')
        if is_mobile == '1':
            redirect("/mobile/main")
        else:
            redirect("/problems")
    else:
        redirect("/user/login?error=Invalid user or Password")

    return {'app': app, 'is_auth': is_auth}


# manage the /. If the user is known, go to problems page.
# Should be /dashboard in the future. If not, go login :)
def get_root():
    user = app.request.get_cookie("user", secret=app.auth_secret)
    if user:
        redirect("/problems")
    elif app.remote_user_enable > 0:
        user_name=None
        if app.remote_user_variable in app.request.headers and app.remote_user_enable == '1':
            user_name = app.request.headers[app.remote_user_variable]
        elif app.remote_user_variable in app.request.environ and app.remote_user_enable == '2':
            user_name = app.request.environ[app.remote_user_variable]
        c = app.datamgr.get_contact(user_name)
        print "Got", c
        if not c:
            print "Warning: You need to have a contact having the same name as your user %s" % user_name
            redirect("/user/login")
        else:
            app.response.set_cookie('user', user_name, secret=app.auth_secret, path='/')
            redirect("/problems")
    else:
        redirect("/user/login")


def login_mobile():
    user = app.get_user_auth()
    if user:
        redirect("/mobile/main")

    err = app.request.GET.get('error', None)
    login_text = app.login_text

    return {'error': err, 'login_text': login_text}

pages = {user_login: {'routes': ['/user/login', '/user/login/'],
                         'view': 'login', 'static': True},
          user_login_redirect: {'routes': ['/login'], 'static': True},
          user_auth: {'routes': ['/user/auth'],
                        'view': 'auth',
                        'method': 'POST', 'static': True},
          user_logout: {'routes': ['/user/logout', '/logout'], 'static': True},
          get_root: {'routes': ['/'], 'static': True},
          login_mobile: {'routes': ['/mobile', '/mobile/'],
                    'view': 'login_mobile', 'static': True}
          }
