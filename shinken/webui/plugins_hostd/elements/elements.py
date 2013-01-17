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

from shinken.webui.bottle import redirect, abort
from shinken.util import to_bool
from shinken.objects import Host
from shinken.objects import Service
from shinken.objects import Timeperiod
from shinken.objects import Contact
from shinken.objects import Command

from local_helper import Helper

### Will be populated by the UI with it's own value
app = None

keys = {'hosts': 'host_name',
        'services': '',
        'timeperiods': 'timeperiod_name',
        'contacts': 'contact_name',
        'commands': 'command_name'
        }


def elements_generic(cls, show_tpls=False):
    # First we look for the user sid
    # so we bail out if it's a false one
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    # Get all entries from db
    #t = getattr(app.db, cls.my_type+'s')
    #cur = t.find({})
    #elts = [cls(i) for i in cur]
    print "GENERIC", cls.my_type
    t = cls.my_type + 's'
    key = keys[t]
    #if cls.my_type == 'host':
    #    print "HOOK HOSTS"
    elts = [cls(i) for i in app.datamgr.get_generics(t, key)]
    print "GOT elements", elts

    # Look for removing or keeping templates
    if not show_tpls:
        print "REMOVING TEMPLATES"
        elts = [e for e in elts if not e.is_tpl()]

    return {'app': app, 'user': user, 'elts': elts, 'elt_type': cls.my_type}


def elements_hosts():
    return elements_generic(Host)


def elements_services():
    return elements_generic(Service, show_tpls=False)


def elements_timeperiods():
    return elements_generic(Timeperiod)


def elements_contacts():
    return elements_generic(Contact)


def elements_commands():
    return elements_generic(Command)


# get data about one specific host
def elements_host(name):
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    #elt = app.db.hosts.find_one({'_id': name})
    elt = app.datamgr.get_host(name)
    if not elt:
        elt = {}
    return {'app': app, 'user': user, 'elt': elt, 'helper': Helper(app)}


# get data about one specific host
def elements_service(name):
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    #elt = app.db.hosts.find_one({'_id': name})
    elt = app.datamgr.get_service(name)
    if not elt:
        elt = {}
    return {'app': app, 'user': user, 'elt': elt, 'helper': Helper(app)}


# get data about one specific contact
def elements_contact(name):
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    elt = app.datamgr.get_contact(name)
    #elt = app.db.contacts.find_one({'_id': name})
    if not elt:
        elt = {}
    return {'app': app, 'user': user, 'elt': elt, 'helper': Helper(app)}


# get data about one specific contact
def elements_command(name):
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    elt = app.datamgr.get_command(name)
    if not elt:
        elt = {}
    return {'app': app, 'user': user, 'elt': elt, 'helper': Helper(app)}


def elements_timeperiod(name):
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    elt = app.datamgr.get_timeperiod(name)
    if not elt:
        elt = {}
    return {'app': app, 'user': user, 'elt': elt, 'helper': Helper(app)}


### New things
def new_host():
    return new_object()


def new_service():
    return new_object()


def new_contact():
    return new_object()


def new_command():
    return new_object()


def new_timeperiod():
    return new_object()


def new_object():
    user = app.get_user_auth()
    if not user:
        redirect("/user/login")

    return {'app': app, 'user': user, 'elt': {}, 'helper': Helper(app)}


def disable_object(cls, name):
    print "Disable object for", cls, name
    t = getattr(app.db, cls)
    d = t.find_one({'_id': name})
    d['_state'] = 'disabled'
    r = t.save(d)
    print "Disabled?", r


def enable_object(cls, name):
    print "Enable object for", cls, name
    t = getattr(app.db, cls)
    d = t.find_one({'_id': name})
    d['_state'] = 'enabled'
    r = t.save(d)
    print "Disabled?", r


def save_object(cls, name):
    print "Save object for", cls, name

    # First we check if the elements is being renamed
    old_name = name
    key = keys[cls]
    new_name = app.request.forms.get(key, None)

    # For service, we must force the old_name and the new_one :(
    if key == '':
        new_name = name

    print "New and old", new_name, old_name
    # For service we must avoid the key check :(
    if not new_name:
        print 'Missing the property %s' % key
        abort(400, 'Missing the property %s' % key)

    print "After?"
    t = getattr(app.db, cls)
    d = t.find_one({'_id': old_name})

    # Maybe we renamed the element? If so, we
    # must delete the old entry before saving the new one
    if new_name != old_name:
        t.remove({'_id': old_name})

    print 'In db', d
    bd_entry = {'_id': new_name}
    if d:
        print 'We got an entry in db', d
        db_entry = d
        bd_entry['_id'] = new_name

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


def save_new_object(cls):
    print "Save new object for", cls
    t = getattr(app.db, cls)
    # Try to get the name of this new object
    key = keys[cls]
    name = app.request.forms.get(key, None)

    # For service such a check must be avoid because there is no real key
    if key != '':
        if name is None or name == '':
            abort(400, "Missing property %s" % key)

    d = t.find_one({'_id': name})
    # Save a new object means that there should not be old one
    # with the same name of course. Or it should be an edit, not a "new"
    if d is not None:
        abort(400, "Already an object with the same name '%s'" % name)

    # Ok, we can save it!
    save_object(cls, name)

pages = {
    # HOSTS
    elements_hosts: {'routes': ['/elements/hosts'], 'view': 'elements_hosts', 'static': True},
    elements_host: {'routes': ['/elements/hosts/:name'], 'view': 'elements_host', 'static': True},
    new_host: {'routes': ['/elements/add/host'], 'view': 'elements_host', 'static': True},

    # Contacts
    elements_contacts: {'routes': ['/elements/contacts'], 'view': 'elements_contacts', 'static': True},
    elements_contact: {'routes': ['/elements/contacts/:name'], 'view': 'elements_contact', 'static': True},
    new_contact: {'routes': ['/elements/add/contact'], 'view': 'elements_contact', 'static': True},

    # Services
    elements_services: {'routes': ['/elements/services'], 'view': 'elements_services', 'static': True},
    elements_service: {'routes': ['/elements/services/:name'], 'view': 'elements_service', 'static': True},
    new_service: {'routes': ['/elements/add/service'], 'view': 'elements_service', 'static': True},


    # Timeperiods
    elements_timeperiods: {'routes': ['/elements/timeperiods'], 'view': 'elements_timeperiods', 'static': True},
    elements_timeperiod: {'routes': ['/elements/timeperiods/:name'], 'view': 'elements_timeperiod', 'static': True},
    new_timeperiod: {'routes': ['/elements/add/timeperiod'], 'view': 'elements_timeperiod', 'static': True},


    # Commands
    elements_commands: {'routes': ['/elements/commands'], 'view': 'elements_commands', 'static': True},
    elements_command: {'routes': ['/elements/commands/:name'], 'view': 'elements_command', 'static': True},
    new_command: {'routes': ['/elements/add/command'], 'view': 'elements_command', 'static': True},


    # Action URI
    disable_object: {'routes': ['/element/q/:cls/disable/:name']},
    enable_object: {'routes': ['/element/q/:cls/enable/:name']},


    # POST backend
    save_object: {'routes': ['/element/q/:cls/save/:name'], 'method': 'POST'},
    save_new_object: {'routes': ['/element/q/:cls/save/'], 'method': 'POST'},
    }
