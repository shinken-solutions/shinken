#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
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

import copy

from item import Item
from itemgroup import Itemgroup, Itemgroups
from shinken.property import BoolProp, IntegerProp, StringProp, DictProp, ListProp
from shinken.log import logger

# It change from hostgroup Class because there is no members
# properties, just the realm_members that we rewrite on it.

class Realm(Itemgroup):
    id = 1  # zero is always a little bit special... like in database
    my_type = 'realm'

    properties = Itemgroup.properties.copy()
    properties.update({
        'id':            IntegerProp(default=0, fill_brok=['full_status']),
        'realm_name':    StringProp(fill_brok=['full_status']),
        # No status_broker_name because it put hosts, not host_name
        'realm_members': ListProp(default=[], split_on_coma=True),
        'higher_realms': ListProp(default=[], split_on_coma=True),
        'default':       BoolProp(default=False),
        'broker_complete_links':       BoolProp(default=False),
        # 'alias': {'required':  True, 'fill_brok': ['full_status']},
        # 'notes': {'required': False, 'default':'', 'fill_brok': ['full_status']},
        # 'notes_url': {'required': False, 'default':'', 'fill_brok': ['full_status']},
        # 'action_url': {'required': False, 'default':'', 'fill_brok': ['full_status']},
    })

    running_properties = Item.running_properties.copy()
    running_properties.update({
        'serialized_confs': DictProp(default={}),
    })

    macros = {
        'REALMNAME': 'realm_name',
        'REALMMEMBERS': 'members',
    }

    def get_name(self):
        return self.realm_name

    def get_realms(self):
        return self.realm_members

    def add_string_member(self, member):
        self.realm_members += ',' + member

    def get_realm_members(self):
        if self.has('realm_members'):
            return [r.strip() for r in self.realm_members]
        else:
            return []

    # We fillfull properties with template ones if need
    # Because hostgroup we call may not have it's members
    # we call get_hosts_by_explosion on it
    def get_realms_by_explosion(self, realms):
        # First we tag the hg so it will not be explode
        # if a son of it already call it
        self.already_explode = True

        # Now the recursive part
        # rec_tag is set to False every HG we explode
        # so if True here, it must be a loop in HG
        # calls... not GOOD!
        if self.rec_tag:
            err = "Error: we've got a loop in realm definition %s" % self.get_name()
            self.configuration_errors.append(err)
            if self.has('members'):
                return self.members
            else:
                return ''

        # Ok, not a loop, we tag it and continue
        self.rec_tag = True

        p_mbrs = self.get_realm_members()
        for p_mbr in p_mbrs:
            p = realms.find_by_name(p_mbr.strip())
            if p is not None:
                value = p.get_realms_by_explosion(realms)
                if value is not None:
                    self.add_string_member(value)

        if self.has('members'):
            return self.members
        else:
            return ''

    def get_all_subs_satellites_by_type(self, sat_type):
        r = copy.copy(getattr(self, sat_type))
        for p in self.realm_members:
            tmps = p.get_all_subs_satellites_by_type(sat_type)
            for s in tmps:
                r.append(s)
        return r

    def count_reactionners(self):
        self.nb_reactionners = 0
        for reactionner in self.reactionners:
            if not reactionner.spare:
                self.nb_reactionners += 1
        for realm in self.higher_realms:
            for reactionner in realm.reactionners:
                if not reactionner.spare and reactionner.manage_sub_realms:
                    self.nb_reactionners += 1

    def count_pollers(self):
        self.nb_pollers = 0
        for poller in self.pollers:
            if not poller.spare:
                self.nb_pollers += 1
        for realm in self.higher_realms:
            for poller in realm.pollers:
                if not poller.spare and poller.manage_sub_realms:
                    self.nb_pollers += 1

    def count_brokers(self):
        self.nb_brokers = 0
        for broker in self.brokers:
            if not broker.spare:
                self.nb_brokers += 1
        for realm in self.higher_realms:
            for broker in realm.brokers:
                if not broker.spare and broker.manage_sub_realms:
                    self.nb_brokers += 1

    def count_receivers(self):
        self.nb_receivers = 0
        for receiver in self.receivers:
            if not receiver.spare:
                self.nb_receivers += 1
        for realm in self.higher_realms:
            for receiver in realm.receivers:
                if not receiver.spare and receiver.manage_sub_realms:
                    self.nb_receivers += 1

    # Return the list of satellites of a certain type
    # like reactionner -> self.reactionners
    def get_satellties_by_type(self, type):
        if hasattr(self, type + 's'):
            return getattr(self, type + 's')
        else:
            logger.debug("[realm] do not have this kind of satellites: %s", type)
            return []


    def fill_potential_satellites_by_type(self, sat_type):
        setattr(self, 'potential_%s' % sat_type, [])
        for satellite in getattr(self, sat_type):
            getattr(self, 'potential_%s' % sat_type).append(satellite)
        for realm in self.higher_realms:
            for satellite in getattr(realm, sat_type):
                if satellite.manage_sub_realms:
                    getattr(self, 'potential_%s' % sat_type).append(satellite)



    # Return the list of potentials satellites of a certain type
    # like reactionner -> self.potential_reactionners
    def get_potential_satellites_by_type(self, type):
        if hasattr(self, 'potential_' + type + 's'):
            return getattr(self, 'potential_' + type + 's')
        else:
            logger.debug("[realm] do not have this kind of satellites: %s", type)
            return []


    # Return the list of potentials satellites of a certain type
    # like reactionner -> self.nb_reactionners
    def get_nb_of_must_have_satellites(self, type):
        if hasattr(self, 'nb_' + type + 's'):
            return getattr(self, 'nb_' + type + 's')
        else:
            logger.debug("[realm] do not have this kind of satellites: %s", type)
            return 0


    # Fill dict of realms for managing the satellites confs
    def prepare_for_satellites_conf(self):
        self.to_satellites = {}
        self.to_satellites['reactionner'] = {}
        self.to_satellites['poller'] = {}
        self.to_satellites['broker'] = {}
        self.to_satellites['receiver'] = {}

        self.to_satellites_need_dispatch = {}
        self.to_satellites_need_dispatch['reactionner'] = {}
        self.to_satellites_need_dispatch['poller'] = {}
        self.to_satellites_need_dispatch['broker'] = {}
        self.to_satellites_need_dispatch['receiver'] = {}

        self.to_satellites_managed_by = {}
        self.to_satellites_managed_by['reactionner'] = {}
        self.to_satellites_managed_by['poller'] = {}
        self.to_satellites_managed_by['broker'] = {}
        self.to_satellites_managed_by['receiver'] = {}

        self.count_reactionners()
        self.fill_potential_satellites_by_type('reactionners')
        self.count_pollers()
        self.fill_potential_satellites_by_type('pollers')
        self.count_brokers()
        self.fill_potential_satellites_by_type('brokers')
        self.count_receivers()
        self.fill_potential_satellites_by_type('receivers')

        s = "%s: (in/potential) (schedulers:%d) (pollers:%d/%d) "\
            "(reactionners:%d/%d) (brokers:%d/%d) (receivers:%d/%d)" % \
            (self.get_name(),
             len(self.schedulers),
             self.nb_pollers, len(self.potential_pollers),
             self.nb_reactionners, len(self.potential_reactionners),
             self.nb_brokers, len(self.potential_brokers),
             self.nb_receivers, len(self.potential_receivers)
             )
        logger.info(s)


    # TODO: find a better name...
    # TODO: and if he goes active?
    def fill_broker_with_poller_reactionner_links(self, broker):
        # First we create/void theses links
        broker.cfg['pollers'] = {}
        broker.cfg['reactionners'] = {}
        broker.cfg['receivers'] = {}

        # First our own level
        for p in self.pollers:
            cfg = p.give_satellite_cfg()
            broker.cfg['pollers'][p.id] = cfg

        for r in self.reactionners:
            cfg = r.give_satellite_cfg()
            broker.cfg['reactionners'][r.id] = cfg

        for b in self.receivers:
            cfg = b.give_satellite_cfg()
            broker.cfg['receivers'][b.id] = cfg

        # Then sub if we must to it
        if broker.manage_sub_realms:
            # Now pollers
            for p in self.get_all_subs_satellites_by_type('pollers'):
                cfg = p.give_satellite_cfg()
                broker.cfg['pollers'][p.id] = cfg

            # Now reactionners
            for r in self.get_all_subs_satellites_by_type('reactionners'):
                cfg = r.give_satellite_cfg()
                broker.cfg['reactionners'][r.id] = cfg

            # Now receivers
            for r in self.get_all_subs_satellites_by_type('receivers'):
                cfg = r.give_satellite_cfg()
                broker.cfg['receivers'][r.id] = cfg


    # Get a conf package of satellites links that can be useful for
    # a scheduler
    def get_satellites_links_for_scheduler(self):
        cfg = {}

        # First we create/void theses links
        cfg['pollers'] = {}
        cfg['reactionners'] = {}

        # First our own level
        for p in self.pollers:
            c = p.give_satellite_cfg()
            cfg['pollers'][p.id] = c

        for r in self.reactionners:
            c = r.give_satellite_cfg()
            cfg['reactionners'][r.id] = c

        # print "***** Preparing a satellites conf for a scheduler", cfg
        return cfg


class Realms(Itemgroups):
    name_property = "realm_name"  # is used for finding hostgroups
    inner_class = Realm

    def get_members_by_name(self, pname):
        realm = self.find_by_name(pname)
        if realm is None:
            return []
        return realm.get_realms()


    def linkify(self):
        self.linkify_p_by_p()

        # prepare list of satellites and confs
        for p in self:
            p.pollers = []
            p.schedulers = []
            p.reactionners = []
            p.brokers = []
            p.receivers = []
            p.packs = []
            p.confs = {}


    # We just search for each realm the others realms
    # and replace the name by the realm
    def linkify_p_by_p(self):
        for p in self.items.values():
            mbrs = p.get_realm_members()
            # The new member list, in id
            new_mbrs = []
            for mbr in mbrs:
                new_mbr = self.find_by_name(mbr)
                if new_mbr is not None:
                    new_mbrs.append(new_mbr)
            # We find the id, we replace the names
            p.realm_members = new_mbrs

        # Now put higher realm in sub realms
        # So after they can
        for p in self.items.values():
            p.higher_realms = []

        for p in self.items.values():
            self.recur_higer_realms(p, p.realm_members)


    # I add the R realm in the sons.higer_realms, and
    # also in the son.sons and so on
    def recur_higer_realms(self, r, sons):
        for sub_p in sons:
            sub_p.higher_realms.append(r)
            # and call for our sons too
            self.recur_higer_realms(r, sub_p.realm_members)


    # Use to fill members with hostgroup_members
    def explode(self):
        # We do not want a same hg to be explode again and again
        # so we tag it
        for tmp_p in self.items.values():
            tmp_p.already_explode = False
        for p in self:
            if p.has('realm_members') and not p.already_explode:
                # get_hosts_by_explosion is a recursive
                # function, so we must tag hg so we do not loop
                for tmp_p in self:
                    tmp_p.rec_tag = False
                p.get_realms_by_explosion(self)

        # We clean the tags
        for tmp_p in self.items.values():
            if hasattr(tmp_p, 'rec_tag'):
                del tmp_p.rec_tag
            del tmp_p.already_explode


    def get_default(self):
        for r in self:
            if getattr(r, 'default', False):
                return r
        return None


    def prepare_for_satellites_conf(self):
        for r in self:
            r.prepare_for_satellites_conf()
