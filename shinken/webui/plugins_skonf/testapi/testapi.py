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
from StringIO import StringIO
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


def check_api_server(api_key):
    print "GO TO CONNEXION"
    error = ''
    results = ''
    c = pycurl.Curl()
    #c.setopt(c.CONNECTTIMEOUT, 5)
    #c.setopt(c.TIMEOUT, 8)
    #c.setopt(c.PROXY, 'http://inthemiddle.com:8080')
    url = "http://127.0.0.1:7765/checkkey/" + api_key
    print "GO TO URL", url
    # Oups, seems that url an unicode are BAD :)
    url = str(url)
    c.setopt(c.URL, url)
    #c.setopt(c.HTTPPOST,[ ("search", search)])

    #c.setopt(c.HTTPPOST, [("file1", (c.FORM_FILE, str(zip_file_p)))])
    c.setopt(c.VERBOSE, 1)

    response = StringIO()
    c.setopt(c.WRITEFUNCTION, response.write)
    r = c.perform()
    response.seek(0)
    status_code = c.getinfo(pycurl.HTTP_CODE)
    # We only parse the json if we got
    if status_code == 200:
        results = json.loads(response.read().replace('\\/', '/'))
    else:
        error = response.read().replace('\\/', '/')

    c.close()

    print "status code: %s" % status_code
    print "Json loaded", results, error
    return (results, error)


# Our page. If the useer call /dummy/TOTO arg1 will be TOTO.
# if it's /dummy/, it will be 'nothing'
def get_page():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
        return

    api_key = app.get_api_key()
    print "API KEY IS", api_key, type(api_key)
    api_error = ''
    results = ''
    if api_key:
        (results, api_error) = check_api_server(api_key)
    else:
        api_error = "You don't have configured your API KEY"

    # we return values for the template (view). But beware, theses values are the
    # only one the tempalte will have, so we must give it an app link and the
    # user we are loggued with (it's a contact object in fact)
    return {'app': app, 'user': user, 'results': results, 'api_error': api_error}

# This is the dict teh webui will try to "load".
#  *here we register one page with both adresses /dummy/:arg1 and /dummy/, both addresses
#   will call the function get_page.
#  * we say taht for this page, we are using the template file dummy (so view/dummy.tpl)
#  * we said this page got some static stuffs. So the webui will match /static/dummy/ to
#    the dummy/htdocs/ directory. Bewere: it will take the plugin name to match.
#  * optional: you can add 'method': 'POST' so this adress will be only available for
#    POST calls. By default it's GET. Look at the lookup module for sample about this.
pages = {get_page: {'routes': ['/testapi'], 'view': 'testapi', 'static': True}}
