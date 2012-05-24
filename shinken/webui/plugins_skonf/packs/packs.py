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
try:
    import json
except ImportError:
    # For old Python version, load
    # simple json (it can be hard json?! It's 2 functions guy!)
    try:
        import simplejson as json
    except ImportError:
        print "Error : you need the json or simplejson module"
        raise


from local_helper import print_cat_tree
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
    if not user:
        redirect("/user/login")
        return

    # Get the categories
    c = pycurl.Curl()
    c.setopt(c.POST, 1)
    #c.setopt(c.CONNECTTIMEOUT, 5)
    #c.setopt(c.TIMEOUT, 8)
    #c.setopt(c.PROXY, 'http://inthemiddle.com:8080')
    c.setopt(c.URL, "http://127.0.0.1:7765/categories")
    c.setopt(c.HTTPPOST,[ ("root", '/')])    
    c.setopt(c.VERBOSE, 1)
    response = StringIO()
    c.setopt(c.WRITEFUNCTION, response.write)
    r = c.perform()
    response.seek(0)
    categories = json.loads(response.read().replace('\\/', '/'))
    status_code = c.getinfo(pycurl.HTTP_CODE)
    print "status code: %s" % status_code
    c.close()
    print "Json loaded", categories


    # Then the tags, like 30
    c = pycurl.Curl()
    c.setopt(c.POST, 1)
    #c.setopt(c.CONNECTTIMEOUT, 5)
    #c.setopt(c.TIMEOUT, 8)
    #c.setopt(c.PROXY, 'http://inthemiddle.com:8080')
    c.setopt(c.URL, "http://127.0.0.1:7765/tags")
    c.setopt(c.HTTPPOST,[ ("nb", '50')])
    c.setopt(c.VERBOSE, 1)
    response = StringIO()
    c.setopt(c.WRITEFUNCTION, response.write)
    r = c.perform()
    response.seek(0)
    raw_tags = json.loads(response.read().replace('\\/', '/'))
    status_code = c.getinfo(pycurl.HTTP_CODE)
    print "status code: %s" % status_code
    c.close()
    print "Json loaded", categories
    # We want small before
    raw_tags.reverse()

    new_tags = {}
    # Compute sizes
    nb_tags = len(raw_tags)
    i = 0
    for (name, occ) in raw_tags:
        i += 1
        size = 1 + float(i)/nb_tags
        new_tags[name] = {'name' : name, 'size' : size, 'occ' : occ}

    # Sort by name
    names = new_tags.keys()
    names.sort()
    
    tags = []
    for name in names:
        tags.append(new_tags[name])

    error = ''
    
    # we return values for the template (view). But beware, theses values are the
    # only one the tempalte will have, so we must give it an app link and the
    # user we are loggued with (it's a contact object in fact)
    return {'app':app, 'user':user, 'error':error, 'results':None, 'search':None, 'categories' : categories, 'tags':tags,  'print_cat_tree':print_cat_tree}


def get_new_packs_result():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")
        return

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
    return {'app':app, 'user':user, 'error':error, 'results':results, 'search':search, 'categories':None, 'tags':None}



def download_pack(uri):
    app.response.content_type = 'application/json'

    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()
    if not user:
        r = {'state' : 401, 'text' : 'Sorry you are not logged!'}
        return json.dumps(r)            

    print "We are asked to download", uri
    c = pycurl.Curl()
    c.setopt(c.HTTPGET, 1)
    c.setopt(c.URL, uri)
    response = StringIO()
    c.setopt(c.WRITEFUNCTION, response.write)
    c.perform()
    c.close()
    response.seek(0)
    buf = response.read(5000000)
    add = response.read(1)
    if add:
        r = {'state' : 400, 'text' : 'Sorry the file is too big!'}
        return json.dumps(r)            

    print "WE get a file os the size", len(buf)
    
    
    r = app.save_pack(buf)
    print "RETURN", r
    return json.dumps(r)

    

pages = {get_packs : { 'routes' : ['/packs'], 'view' : 'packs', 'static' : True},
         get_new_packs : { 'routes' : ['/getpacks'], 'view' : 'getpacks', 'static' : True},
         get_new_packs_result : { 'routes' : ['/getpacks'], 'method' : 'POST', 'view' : 'getpacks', 'static' : True},
         download_pack : { 'routes' : ['/download/:uri#.+#'], 'view':None, 'static' : True},
         }

