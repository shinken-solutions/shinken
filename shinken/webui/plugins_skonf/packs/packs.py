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

import pycurl
import json
from StringIO import StringIO

from shinken.webui.bottle import redirect

### Will be populated by the UI with it's own value
app = None

# Our page. If the useer call /dummy/TOTO arg1 will be TOTO.
# if it's /dummy/, it will be 'nothing'
def get_packs():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    # we return values for the template (view). But beware, theses values are the
    # only one the tempalte will have, so we must give it an app link and the
    # user we are loggued with (it's a contact object in fact)
    return {'app' : app, 'user' : user}


def get_new_packs():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    error = ''
    
    # we return values for the template (view). But beware, theses values are the
    # only one the tempalte will have, so we must give it an app link and the
    # user we are loggued with (it's a contact object in fact)
    return {'app':app, 'user':user, 'error':error, 'results':None, 'search':None}


def get_new_packs_result():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    search = app.request.forms.get('search')
    error = ''
    results = []
    if search:
        c = pycurl.Curl()
        c.setopt(c.POST, 1)
        #c.setopt(c.CONNECTTIMEOUT, 5)
        #c.setopt(c.TIMEOUT, 8)
        #c.setopt(c.PROXY, 'http://inthemiddle.com:8080')
        c.setopt(c.URL, "http://127.0.0.1:7765/search")
        c.setopt(c.HTTPPOST,[ ("search", search)])
    
        #c.setopt(c.HTTPPOST, [("file1", (c.FORM_FILE, str(zip_file_p)))])
        c.setopt(c.VERBOSE, 1)

        response = StringIO()
        c.setopt(c.WRITEFUNCTION, response.write)
        r = c.perform()
        response.seek(0)
        results = json.loads(response.read().replace('\\/', '/'))
        status_code = c.getinfo(pycurl.HTTP_CODE)
        print "status code: %s" % status_code
        c.close()
        print "Json loaded", results
    else:
        error = 'You forgot the search entry'

    # we return values for the template (view). But beware, theses values are the
    # only one the tempalte will have, so we must give it an app link and the
    # user we are loggued with (it's a contact object in fact)
    return {'app':app, 'user':user, 'error':error, 'results':results, 'search':search}



pages = {get_packs : { 'routes' : ['/packs'], 'view' : 'packs', 'static' : True},
         get_new_packs : { 'routes' : ['/getpacks'], 'view' : 'getpacks', 'static' : True},
         get_new_packs_result : { 'routes' : ['/getpacks'], 'method' : 'POST', 'view' : 'getpacks', 'static' : True},
         }

