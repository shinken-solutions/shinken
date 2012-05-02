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
from shinken.objects import Service
from shinken.objects import Timeperiod
from shinken.objects import Contact
from shinken.objects import Command

from local_helper import Helper

### Will be populated by the UI with it's own value
app = None

def objects_generic(cls):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()

    if not user:
        redirect("/user/login")
    
    
    # Get all entries from db
    t = getattr(app.db, cls.my_type+'s')
    cur = t.find({})
    elts = [cls(i) for i in cur]

    return {'app' : app, 'user' : user, 'elts' : elts, 'elt_type' : cls.my_type}


def objects_hosts():
    return objects_generic(Host)


def objects_services():
    return objects_generic(Service)

def objects_timeperiods():
    return objects_generic(Timeperiod)

def objects_contacts():
    return objects_generic(Contact)

def objects_commands():
    return objects_generic(Command)


# get data about one specific host
def objects_host(name):
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    elt = app.db.hosts.find_one({'_id' : name})
    return {'app' : app, 'user' : user, 'elt' : elt, 'helper' : Helper(app)}
    


def disable_object(cls, name):
    print "Disable object for", cls, name
    t = getattr(app.db, cls)
    d = t.find_one({'_id' : name})
    d['_state'] = 'disabled'
    r = t.save(d)
    print "Disabled?", r


def enable_object(cls, name):
    print "Enable object for", cls, name
    t = getattr(app.db, cls)
    d = t.find_one({'_id' : name})
    d['_state'] = 'enabled'
    r = t.save(d)
    print "Disabled?", r



def save_object(cls, name):
    print "Save object for", cls, name
    t = getattr(app.db, cls)
    d = t.find_one({'_id' : name})
    print 'In db', d
    bd_entry = {'_id' : name}
    if d:
        print 'We got an entry in db', d
        db_entry = d
        bd_entry['_id'] = name
        
    print 'Dump form', app.request.forms.__dict__
    for k in app.request.forms:
        #print "K", k
        v = str(app.request.forms.get(k))
        # the value can be '' or something else. 
        # -> '' means not set
        # -> else set the value :)
        if v == '' and k in bd_entry:
            del bd_entry[k]
        if v != '':
            bd_entry[k] = v

    print 'We will save our object in db'
    print bd_entry
    t.save(bd_entry)
            
        


pages = {objects_hosts : { 'routes' : ['/objects/hosts'], 'view' : 'objects_hosts', 'static' : True},
         objects_services : { 'routes' : ['/objects/services'], 'view' : 'objects_hosts', 'static' : True},
         objects_timeperiods : { 'routes' : ['/objects/timeperiods'], 'view' : 'objects_hosts', 'static' : True},
         objects_contacts : { 'routes' : ['/objects/contacts'], 'view' : 'objects_hosts', 'static' : True},
         objects_commands : { 'routes' : ['/objects/commands'], 'view' : 'objects_hosts', 'static' : True},
         objects_host : { 'routes' : ['/objects/hosts/:name'], 'view' : 'objects_host', 'static' : True},
         disable_object : { 'routes' : ['/object/q/:cls/disable/:name']},
         enable_object : { 'routes' : ['/object/q/:cls/enable/:name']},
         save_object : { 'routes' : ['/object/q/:cls/save/:name'], 'method' : 'POST'},
         }

