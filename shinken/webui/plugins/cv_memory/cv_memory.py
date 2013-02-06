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
from pprint import pprint

import xmlrpclib
import json


### Will be populated by the UI with it's own value
app = None

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
        redirect("/user/login")

    # Ok, we can lookup it
    h = app.datamgr.get_host(hname)

    ps = get_processes(h)
    
    return {'app': app, 'elt': h, 'ps':ps}




# Void plugin
pages = {get_page: {'routes': ['/cv/memory/:hname'], 'view': 'cv_memory', 'static': True}}
