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

import time
import random

from shinken.webui.bottle import redirect
from shinken.util import to_bool
from shinken.objects import Host


### Will be populated by the UI with it's own value
app = None

def objects_hosts():
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")


    cur = app.db.hosts.find({})
    hosts = [Host(h) for h in cur]

    return {'app' : app, 'user' : user, 'hosts' : hosts}


def disable_host(name):
    d = app.db.hosts.find_one({'_id' : name})
    d['_state'] = 'disabled'
    r = app.db.hosts.save(d)
    print "Disabled?", r


def enable_host(name):
    d = app.db.hosts.find_one({'_id' : name})
    d['_state'] = 'enabled'
    r = app.db.hosts.save(d)
    print "Enabled?", r



pages = {objects_hosts : { 'routes' : ['/objects/hosts'], 'view' : 'objects_hosts', 'static' : True},
         disable_host : { 'routes' : ['/object/q/host/disable/:name']},
         enable_host : { 'routes' : ['/object/q/host/enable/:name']},
         }

