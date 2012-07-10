#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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
import socket

import shinken.pyro_wrapper as pyro
Pyro = pyro.Pyro
PYRO_VERSION = pyro.PYRO_VERSION

from shinken.util import get_obj_name_two_args_and_void
from shinken.objects import Item, Items
from shinken.property import BoolProp, IntegerProp, StringProp, ListProp, DictProp, AddrProp
from shinken.log import logger

# Pack of common Pyro exceptions
Pyro_exp_pack = (Pyro.errors.ProtocolError, Pyro.errors.URIError, \
                    Pyro.errors.CommunicationError, \
                    Pyro.errors.DaemonError)


class SatelliteLink(Item):
    """SatelliteLink is a common Class for link to satellite for
    Arbiter with Conf Dispatcher.

    """
    # id = 0 each Class will have it's own id

    properties = Item.properties.copy()
    properties.update({
        'address':         StringProp(fill_brok=['full_status']),
        'timeout':         IntegerProp(default='3', fill_brok=['full_status']),
        'data_timeout':    IntegerProp(default='120', fill_brok=['full_status']),
        'check_interval':  IntegerProp(default='60', fill_brok=['full_status']),
        'max_check_attempts': IntegerProp(default='3', fill_brok=['full_status']),
        'spare':              BoolProp(default='0', fill_brok=['full_status']),
        'manage_sub_realms':  BoolProp(default='1', fill_brok=['full_status']),
        'manage_arbiters':    BoolProp(default='0', fill_brok=['full_status'], to_send=True),
        'modules':            ListProp(default='', to_send=True),
        'polling_interval':   IntegerProp(default='1', fill_brok=['full_status'], to_send=True),
        'use_timezone':       StringProp(default='NOTSET', to_send=True),
        'realm':              StringProp(default='', fill_brok=['full_status'], brok_transformation=get_obj_name_two_args_and_void),
        'satellitemap':       DictProp(default=None, elts_prop=AddrProp, to_send=True, override=True),
    })

    running_properties = Item.running_properties.copy()
    running_properties.update({
        'con':                  StringProp(default=None),
        'alive':                StringProp(default=True, fill_brok=['full_status']),
        'broks':                StringProp(default=[]),
        'attempt':              StringProp(default=0, fill_brok=['full_status']), # the number of failed attempt
        'reachable':            StringProp(default=False, fill_brok=['full_status']), # can be network ask or not (dead or check in timeout or error)
        'last_check':           IntegerProp(default=0, fill_brok=['full_status']),
        'managed_confs':        StringProp(default={}),
    })

    def __init__(self, *args, **kwargs):
        super(SatelliteLink, self).__init__(*args, **kwargs)

        self.arb_satmap = {'address': '0.0.0.0', 'port': 0}
        if hasattr(self, 'address'):
            self.arb_satmap['address'] = self.address
        if hasattr(self, 'port'):
            try:
                self.arb_satmap['port'] = int(self.port)
            except:
                pass

    def set_arbiter_satellitemap(self, satellitemap):
        """
            arb_satmap is the satellitemap in current context:
                - A SatelliteLink is owned by an Arbiter
                - satellitemap attribute of SatelliteLink is the map defined IN THE satellite configuration
                  but for creating connections, we need the have the satellitemap of the Arbiter
        """
        self.arb_satmap = {'address': self.address, 'port': self.port}
        self.arb_satmap.update(satellitemap)

    def create_connection(self):
        try:
            self.uri = pyro.create_uri(self.arb_satmap['address'], self.arb_satmap['port'], "ForArbiter", self.__class__.use_ssl)
            # By default Pyro got problem in connect() function that can take
            # long seconds to raise a timeout. And even with the _setTimeout()
            # call. So we change the whole default connect() timeout
            socket.setdefaulttimeout(self.timeout)
            self.con = pyro.getProxy(self.uri)
            # But the multiprocessing module is not copatible with it!
            # so we must disable it imadiatly after
            socket.setdefaulttimeout(None)
            pyro.set_timeout(self.con, self.timeout)
        except Pyro_exp_pack, exp:
            # But the multiprocessing module is not compatible with it!
            # so we must disable it imadiatly after
            socket.setdefaulttimeout(None)
            self.con = None
            logger.error("Creating connection for %s: %s" % (self.get_name(), str(exp)))

    def put_conf(self, conf):

        if self.con is None:
            self.create_connection()
        #print "Connection is OK, now we put conf", conf
        #print "Try to put conf:", conf

        # Maybe the connexion was not ok, bail out
        if not self.con:
            return False

        try:
            pyro.set_timeout(self.con, self.data_timeout)
            self.con.put_conf(conf)
            pyro.set_timeout(self.con, self.timeout)
            return True
        except Pyro_exp_pack, exp:
            self.con = None
            logger.error(''.join(PYRO_VERSION < "4.0" and Pyro.util.getPyroTraceback(exp) or Pyro.util.getPyroTraceback()))
            return False

    # Get and clean all of our broks
    def get_all_broks(self):
        res = self.broks
        self.broks = []
        return res

    # Set alive, reachable, and reset attemps.
    # If we change state, raise a status brok update
    def set_alive(self):
        was_alive = self.alive
        self.alive = True
        self.attempt = 0
        self.reachable = True

        # We came from dead to alive
        # so we must add a brok update
        if not was_alive:
            b = self.get_update_status_brok()
            self.broks.append(b)

    def set_dead(self):
        was_alive = self.alive
        self.alive = False
        self.con = None

        # We are dead now. Must raise
        # a brok to say it
        if was_alive:
            logger.warning("Setting the satellite %s to a dead state." % self.get_name())
            b = self.get_update_status_brok()
            self.broks.append(b)

    # Go in reachable=False and add a failed attempt
    # if we reach the max, go dead
    def add_failed_check_attempt(self, reason=''):
        self.reachable = False
        self.attempt += 1
        self.attempt = min(self.attempt, self.max_check_attempts)
        # Don't need to warn again and again if the satellite is already dead
        if self.alive:
            logger.warning("Add failed attempt to %s (%d/%d) %s" % (self.get_name(), self.attempt, self.max_check_attempts, reason))

        # check when we just go HARD (dead)
        if self.attempt == self.max_check_attempts:
            self.set_dead()

    # Update satellite info each self.check_interval seconds
    # so we smooth arbiter actions for just useful actions
    # and not cry for a little timeout
    def update_infos(self):
        # First look if it's not too early to ping
        now = time.time()
        since_last_check = now - self.last_check
        if since_last_check < self.check_interval:
            return

        self.last_check = now

        # We ping and update the managed list
        self.ping()
        self.update_managed_list()

        # Update the state of this element
        b = self.get_update_status_brok()
        self.broks.append(b)

    # The elements just got a new conf_id, we put it in our list
    # because maybe the satellite is too busy to answer now
    def known_conf_managed_push(self, cfg_id, push_flavor):
        self.managed_confs[cfg_id] = push_flavor

    def ping(self):
        print "Pinging %s" % self.get_name(),
        try:
            if self.con is None:
                self.create_connection()
            print " (%s)" % self.uri

            # If the connection failed to initialize, bail out
            if self.con is None:
                self.add_failed_check_attempt()
                return

            r = self.con.ping()
            # Should return us pong string
            if r == 'pong':
                self.set_alive()
            else:
                self.add_failed_check_attempt()
        except Pyro_exp_pack, exp:
            print  # flush previous print
            self.add_failed_check_attempt(reason=str(exp))

    def wait_new_conf(self):
        if self.con is None:
            self.create_connection()
        try:
            self.con.wait_new_conf()
            return True
        except Pyro_exp_pack, exp:
            self.con = None
            return False

    # To know if the satellite have a conf (magic_hash = None)
    # OR to know if the satellite have THIS conf (magic_hash != None)
    # Magic_hash is for arbiter check only
    def have_conf(self, magic_hash=None):
        if self.con is None:
            self.create_connection()

        # If the connection failed to initialize, bail out
        if self.con is None:
            return False


        try:
            if magic_hash is None:
                r = self.con.have_conf()
            else:
                r = self.con.have_conf(magic_hash)
            # Protect against bad Pyro return
            if not isinstance(r, bool):
                return False
            return r
        except Pyro_exp_pack, exp:
            self.con = None
            return False

    # To know if a receiver got a conf or not
    def got_conf(self):
        if self.con is None:
            self.create_connection()

        # If the connection failed to initialize, bail out
        if self.con is None:
            return False


        try:
            r = self.con.got_conf()
            # Protect against bad Pyro return
            if not isinstance(r, bool):
                return False
            return r
        except Pyro_exp_pack, exp:
            self.con = None
            return False

    def remove_from_conf(self, sched_id):
        if self.con is None:
            self.create_connection()

        # If the connection failed to initialize, bail out
        if self.con is None:
            return

        try:
            self.con.remove_from_conf(sched_id)
            return True
        except Pyro_exp_pack, exp:
            self.con = None
            return False

    def update_managed_list(self):
        if self.con is None:
            self.create_connection()

        # If the connection failed to initialize, bail out
        if self.con is None:
            self.managed_confs = {}
            return

        try:
            tab = self.con.what_i_managed()
            #print "[%s]What i managed raw value is %s" % (self.get_name(), tab)
            # Protect against bad Pyro return
            if not isinstance(tab, dict):
                self.con = None
                self.managed_confs = {}
            # We can update our list now
            self.managed_confs = tab
        except Pyro_exp_pack, exp:
            # A timeout is not a crime, put this case aside
            if type(exp) == Pyro.errors.TimeoutError:
                return
            self.con = None
            #print "[%s]What i managed: Got exception: %s %s %s" % (self.get_name(), exp, type(exp), exp.__dict__)
            self.managed_confs = {}

    # Return True if the satelltie said to managed a configuration
    def do_i_manage(self, cfg_id, push_flavor):
        # If not even the cfg_id in the managed_conf, baid out
        if not cfg_id in self.managed_confs:
            return False

        # maybe it's in but with a false push_flavor. check it :)
        return self.managed_confs[cfg_id] == push_flavor

    def push_broks(self, broks):
        if self.con is None:
            self.create_connection()

        # If the connection failed to initialize, bail out
        if self.con is None:
            return False


        try:
            return self.con.push_broks(broks)
        except Pyro_exp_pack, exp:
            self.con = None
            return False

    def get_external_commands(self):
        if self.con is None:
            self.create_connection()

        # If the connection failed to initialize, bail out
        if self.con is None:
            return []


        try:
            tab = self.con.get_external_commands()
            # Protect against bad Pyro return
            if not isinstance(tab, list):
                self.con = None
                return []
            return tab
        except Pyro_exp_pack, exp:
            self.con = None
            return []
        except AttributeError:
            self.con = None
            return []

    def prepare_for_conf(self):
        self.cfg = {'global': {}, 'schedulers': {}, 'arbiters': {}}
        properties = self.__class__.properties
        for prop, entry in properties.items():
            if entry.to_send:
                self.cfg['global'][prop] = getattr(self, prop)

    # Some parameters for satellites are not defined in the satellites conf
    # but in the global configuration. We can pass them in the global
    # property
    def add_global_conf_parameters(self, params):
        for prop in params:
            self.cfg['global'][prop] = params[prop]

    def get_my_type(self):
        return self.__class__.my_type

    # Here for poller and reactionner. Scheduler have its own function
    def give_satellite_cfg(self):
        return {'port': self.port,
                'address': self.address,
                'name': self.get_name(),
                'instance_id': self.id,
                'active': True,
                'passive': self.passive,
                'poller_tags': getattr(self, 'poller_tags', []),
                'reactionner_tags': getattr(self, 'reactionner_tags', [])}

    # Call by pickle for dataify the downtime
    # because we DO NOT WANT REF in this pickleisation!
    def __getstate__(self):
        cls = self.__class__
        # id is not in *_properties
        res = {'id': self.id}
        for prop in cls.properties:
            if prop != 'realm':
                if hasattr(self, prop):
                    res[prop] = getattr(self, prop)
        for prop in cls.running_properties:
            if prop != 'con':
                if hasattr(self, prop):
                    res[prop] = getattr(self, prop)
        return res

    # Inverted function of getstate
    def __setstate__(self, state):
        cls = self.__class__

        self.id = state['id']
        for prop in cls.properties:
            if prop in state:
                setattr(self, prop, state[prop])
        for prop in cls.running_properties:
            if prop in state:
                setattr(self, prop, state[prop])
        # con needs to be explicitely set:
        self.con = None


class SatelliteLinks(Items):
    """Please Add a Docstring to describe the class here"""

    # name_property = "name"
    # inner_class = SchedulerLink

    # We must have a realm property, so we find our realm
    def linkify(self, realms, modules):
        self.linkify_s_by_p(realms)
        self.linkify_s_by_plug(modules)

    def linkify_s_by_p(self, realms):
        for s in self:
            p_name = s.realm.strip()
            # If no realm name, take the default one
            if p_name == '':
                p = realms.get_default()
                s.realm = p
            else:  # find the realm one
                p = realms.find_by_name(p_name)
                s.realm = p
            # Check if what we get is OK or not
            if p is not None:
                s.register_to_my_realm()
            else:
                err = "The %s %s got a unknown realm '%s'" % (s.__class__.my_type, s.get_name(), p_name)
                s.configuration_errors.append(err)
                #print err

    def linkify_s_by_plug(self, modules):
        for s in self:
            new_modules = []
            for plug_name in s.modules:
                plug_name = plug_name.strip()
                # don't tread void names
                if plug_name == '':
                    continue

                plug = modules.find_by_name(plug_name)
                if plug is not None:
                    new_modules.append(plug)
                else:
                    err = "Error: the module %s is unknown for %s" % (plug_name, s.get_name())
                    s.configuration_errors.append(err)
            s.modules = new_modules
