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


import types
from shinken.objects import Contact
from shinken.objects import NotificationWay
from shinken.misc.regenerator import Regenerator
from shinken.util import safe_print, get_obj_full_name


def itersorted(self, authuser=None):
    if authuser and authuser in self._id_contact_heap:
        # return only items belonging to this contact
        for _, hid in self._id_contact_heap[authuser]:
            yield self.items[hid]
    elif not authuser:
        # return all items
        for _, hid in self._id_heap:
            yield self.items[hid]
    # if authuser and authuser not in self._id_contact_heap:
    # we do nothing, so the caller gets an empty list


class LiveStatusRegenerator(Regenerator):
    def __init__(self, service_authorization_strict=False, group_authorization_strict=True):
        super(self.__class__, self).__init__()
        self.service_authorization_strict = service_authorization_strict
        self.group_authorization_strict = group_authorization_strict

    def all_done_linking(self, inst_id):
        """In addition to the original all_done_linking our items will get sorted"""
        
        # We will relink all objects if need. If we are in a scheduler, this function will just bailout
        # because it's not need :)
        super(self.__class__, self).all_done_linking(inst_id)

        # now sort the item collections by name
        safe_print("SORTING HOSTS AND SERVICES")
        # First install a new attribute _id_heap, which holds the
        # item ids in sorted order
        setattr(self.services, '_id_heap', [(get_obj_full_name(v), k) for (k, v) in self.services.items.iteritems()])
        self.services._id_heap.sort(key=lambda x: x[0])
        setattr(self.hosts, '_id_heap', [(get_obj_full_name(v), k) for (k, v) in self.hosts.items.iteritems()])
        self.hosts._id_heap.sort(key=lambda x: x[0])
        setattr(self.contacts, '_id_heap', [(get_obj_full_name(v), k) for (k, v) in self.contacts.items.iteritems()])
        self.contacts._id_heap.sort(key=lambda x: x[0])
        setattr(self.servicegroups, '_id_heap', [(get_obj_full_name(v), k) for (k, v) in self.servicegroups.items.iteritems()])
        self.servicegroups._id_heap.sort(key=lambda x: x[0])
        setattr(self.hostgroups, '_id_heap', [(get_obj_full_name(v), k) for (k, v) in self.hostgroups.items.iteritems()])
        self.hostgroups._id_heap.sort(key=lambda x: x[0])
        setattr(self.contactgroups, '_id_heap', [(get_obj_full_name(v), k) for (k, v) in self.contactgroups.items.iteritems()])
        self.contactgroups._id_heap.sort(key=lambda x: x[0])
        # Then install a method for accessing the lists' elements in sorted order
        setattr(self.services, '__itersorted__', types.MethodType(itersorted, self.services))
        setattr(self.hosts, '__itersorted__', types.MethodType(itersorted, self.hosts))
        setattr(self.contacts, '__itersorted__', types.MethodType(itersorted, self.contacts))
        setattr(self.servicegroups, '__itersorted__', types.MethodType(itersorted, self.servicegroups))
        setattr(self.hostgroups, '__itersorted__', types.MethodType(itersorted, self.hostgroups))
        setattr(self.contactgroups, '__itersorted__', types.MethodType(itersorted, self.contactgroups))

        # Speedup authUser requests by populating _id_contact_heap with contact-names as key and 
        # an array with the associated service ids
        setattr(self.hosts, '_id_contact_heap', dict())
        setattr(self.services, '_id_contact_heap', dict())
        setattr(self.hostgroups, '_id_contact_heap', dict())
        setattr(self.servicegroups, '_id_contact_heap', dict())

        [self.hosts._id_contact_heap.setdefault(get_obj_full_name(c), []).append((get_obj_full_name(v), k)) for (k, v) in self.hosts.items.iteritems() for c in v.contacts]
        for c in self.hosts._id_contact_heap.keys():
            self.hosts._id_contact_heap[c].sort(key=lambda x: x[0])

        # strict: one must be an explicity contact of a service in order to see it.
        if self.service_authorization_strict:
            [self.services._id_contact_heap.setdefault(get_obj_full_name(c), []).append((get_obj_full_name(v), k)) for (k, v) in self.services.items.iteritems() for c in v.contacts]
        else:
            # 1. every host contact automatically becomes a service contact
            [self.services._id_contact_heap.setdefault(get_obj_full_name(c), []).append((get_obj_full_name(v), k)) for (k, v) in self.services.items.iteritems () for c in v.host.contacts]
            # 2. explicit service contacts
            [self.services._id_contact_heap.setdefault(get_obj_full_name(c), []).append((get_obj_full_name(v), k)) for (k, v) in self.services.items.iteritems () for c in v.contacts]
        # services without contacts inherit the host's contacts (no matter of strict or loose)
        [self.services._id_contact_heap.setdefault(get_obj_full_name(c), []).append((get_obj_full_name(v), k)) for (k, v) in self.services.items.iteritems() if not v.contacts for c in v.host.contacts]
        for c in self.services._id_contact_heap.keys():
            # remove duplicates
            self.services._id_contact_heap[c] = list(set(self.services._id_contact_heap[c]))
            self.services._id_contact_heap[c].sort(key=lambda x: x[0])


        if self.group_authorization_strict:
            for c in self.hosts._id_contact_heap.keys():
                # only host contacts can be hostgroup-contacts at all
                # now, which hosts does the contact know?
                contact_host_ids = set([h[1] for h in self.hosts._id_contact_heap[c]])
                for (k, v) in self.hostgroups.items.iteritems():
                    # now look if c is contact of all v.members
                    # we already know the hosts for which c is a contact
                    # self.hosts._id_contact_heap[c] is [(hostname, id), (hostname, id)
                    hostgroup_host_ids = set([h.id for h in v.members])
                    # if all of the hostgroup_host_ids are in contact_host_ids
                    # then the hostgroup belongs to the contact
                    if hostgroup_host_ids <= contact_host_ids:
                        self.hostgroups._id_contact_heap.setdefault(c, []).append((v.get_name(), v.id))
            for c in self.services._id_contact_heap.keys():
                # only service contacts can be servicegroup-contacts at all
                # now, which service does the contact know?
                contact_service_ids = set([h[1] for h in self.services._id_contact_heap[c]])
                for (k, v) in self.servicegroups.items.iteritems():
                    # now look if c is contact of all v.members
                    # we already know the services for which c is a contact
                    # self.services._id_contact_heap[c] is [(svcdesc, id), (svcdesc, id)
                    servicegroup_service_ids = set([h.id for h in v.members])
                    # if all of the servicegroup_service_ids are in contact_service_ids
                    # then the servicegroup belongs to the contact
                    print "%-10s %-15s %s <= %s" % (c, v.get_name(), servicegroup_service_ids, contact_service_ids)
                    if servicegroup_service_ids <= contact_service_ids:
                        self.servicegroups._id_contact_heap.setdefault(c, []).append((v.get_name(), v.id))
        else:
            # loose: a contact of a member becomes contact of the whole group
            [self.hostgroups._id_contact_heap.setdefault(get_obj_full_name(c), []).append((get_obj_full_name(v), k)) for (k, v) in self.hostgroups.items.iteritems() for h in v.members for c in h.contacts]
            [self.servicegroups._id_contact_heap.setdefault(get_obj_full_name(c), []).append((get_obj_full_name(v), k)) for (k, v) in self.servicegroups.items.iteritems() for s in v.members for c in s.contacts] # todo: look at mk-livestatus. what about service's host contacts?
        for c in self.hostgroups._id_contact_heap.keys():
            # remove duplicates
            self.hostgroups._id_contact_heap[c] = list(set(self.hostgroups._id_contact_heap[c]))
            self.hostgroups._id_contact_heap[c].sort(key=lambda x: x[0])
        for c in self.servicegroups._id_contact_heap.keys():
            # remove duplicates
            self.servicegroups._id_contact_heap[c] = list(set(self.servicegroups._id_contact_heap[c]))
            self.servicegroups._id_contact_heap[c].sort(key=lambda x: x[0])
 

        # Everything is new now. We should clean the cache
        self.cache.wipeout()


    def manage_initial_contact_status_brok(self, b):
        """overwrite it, because the original method deletes some values"""
        data = b.data
        cname = data['contact_name']
        safe_print("Contact with data", data)
        c = self.contacts.find_by_name(cname)
        if c:
            self.update_element(c, data)
        else:
            safe_print("Creating Contact:", cname)
            c = Contact({})
            self.update_element(c, data)
            self.contacts[c.id] = c

        # Now manage notification ways too
        # Same than for contacts. We create or
        # update
        nws = c.notificationways
        safe_print("Got notif ways", nws)
        new_notifways = []
        for cnw in nws:
            nwname = cnw.notificationway_name
            nw = self.notificationways.find_by_name(nwname)
            if not nw:
                safe_print("Creating notif way", nwname)
                nw = NotificationWay([])
                self.notificationways[nw.id] = nw
            # Now update it
            for prop in NotificationWay.properties:
                if hasattr(cnw, prop):
                    setattr(nw, prop, getattr(cnw, prop))
            new_notifways.append(nw)

            # Linking the notification way
            # With commands
            self.linkify_commands(nw, 'host_notification_commands')
            self.linkify_commands(nw, 'service_notification_commands')


            # Now link timeperiods
            self.linkify_a_timeperiod(nw, 'host_notification_period')
            self.linkify_a_timeperiod(nw, 'service_notification_period')

        c.notificationways = new_notifways

        # Ok, declare this contact now :)
        # And notif ways too
        self.contacts.create_reversed_list()
        self.notificationways.create_reversed_list()

    def register_cache(self, cache):
        self.cache = cache

    def before_after_hook(self, brok, obj):
        self.cache.impact_assessment(brok, obj)
