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

from pprint import pprint

import xmlrpclib
import socket
import json


### Will be populated by the UI with it's own value
app = None

def fancy_units(num):
    for x in ['','KB','MB','GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


def get_processes(h):

    addr = h.address
    
    gs = xmlrpclib.ServerProxy('http://%s:%d' % (addr, 61209))
    # 10s max to aswer
    gs.sock.timeout = 10
    ps = json.loads(gs.getProcessList())
    

    return ps


def get_page(hname):

    print "MEMORY??"
    
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        app.bottle.redirect("/user/login")

    # Ok, we can lookup it
    h = app.datamgr.get_host(hname)
    error = ''
    ps = []
    try:
        ps = get_processes(h)
    except (xmlrpclib.Error, socket.error), exp:
        error = str(exp)
        return {'app': app, 'elt': h, 'ps':ps, 'fancy_units':fancy_units, 'error' : error}
        
    return {'app': app, 'elt': h, 'ps':ps, 'fancy_units':fancy_units, 'error' : error}


def get_page_proc(hname):
    return get_page(hname)


# Void plugin
pages = {get_page: {'routes': ['/cv/memory/:hname'], 'view': 'cv_memory', 'static': True},
         get_page_proc: {'routes': ['/cv/processes/:hname'], 'view': 'cv_processes', 'static': True}
         }
