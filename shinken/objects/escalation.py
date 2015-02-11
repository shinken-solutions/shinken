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

from item import Item, Items

from shinken.util import strip_and_uniq
from shinken.property import BoolProp, IntegerProp, StringProp, ListProp
from shinken.log import logger

_special_properties = ('contacts', 'contact_groups',
                       'first_notification_time', 'last_notification_time')
_special_properties_time_based = ('contacts', 'contact_groups',
                                  'first_notification', 'last_notification')


class Escalation(Item):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'escalation'

    properties = Item.properties.copy()
    properties.update({
        'escalation_name':      StringProp(),
        'first_notification':   IntegerProp(),
        'last_notification':    IntegerProp(),
        'first_notification_time': IntegerProp(),
        'last_notification_time': IntegerProp(),
        # by default don't use the notification_interval defined in
        # the escalation, but the one defined by the object
        'notification_interval': IntegerProp(default=-1),
        'escalation_period':    StringProp(default=''),
        'escalation_options':   ListProp(default=['d', 'u', 'r', 'w', 'c'], split_on_coma=True),
        'contacts':             ListProp(default=[], split_on_coma=True),
        'contact_groups':       ListProp(default=[], split_on_coma=True),
    })

    running_properties = Item.running_properties.copy()
    running_properties.update({
        'time_based': BoolProp(default=False),
    })

    # For debugging purpose only (nice name)
    def get_name(self):
        return self.escalation_name

    # Return True if:
    # *time in in escalation_period or we do not have escalation_period
    # *status is in escalation_options
    # *the notification number is in our interval [[first_notification .. last_notification]]
    # if we are a classic escalation.
    # *If we are time based, we check if the time that we were in notification
    # is in our time interval
    def is_eligible(self, t, status, notif_number, in_notif_time, interval):
        small_states = {
            'WARNING': 'w',    'UNKNOWN': 'u',     'CRITICAL': 'c',
            'RECOVERY': 'r',   'FLAPPING': 'f',    'DOWNTIME': 's',
            'DOWN': 'd',       'UNREACHABLE': 'u', 'OK': 'o', 'UP': 'o'
        }

        # If we are not time based, we check notification numbers:
        if not self.time_based:
            # Begin with the easy cases
            if notif_number < self.first_notification:
                return False

            # self.last_notification = 0 mean no end
            if self.last_notification != 0 and notif_number > self.last_notification:
                return False
        # Else we are time based, we must check for the good value
        else:
            # Begin with the easy cases
            if in_notif_time < self.first_notification_time * interval:
                return False

            # self.last_notification = 0 mean no end
            if self.last_notification_time != 0 and \
                    in_notif_time > self.last_notification_time * interval:
                return False

        # If our status is not good, we bail out too
        if status in small_states and small_states[status] not in self.escalation_options:
            return False

        # Maybe the time is not in our escalation_period
        if self.escalation_period is not None and not self.escalation_period.is_time_valid(t):
            return False

        # Ok, I do not see why not escalade. So it's True :)
        return True

    # t = the reference time
    def get_next_notif_time(self, t_wished, status, creation_time, interval):
        small_states = {'WARNING': 'w', 'UNKNOWN': 'u', 'CRITICAL': 'c',
                        'RECOVERY': 'r', 'FLAPPING': 'f', 'DOWNTIME': 's',
                        'DOWN': 'd', 'UNREACHABLE': 'u', 'OK': 'o', 'UP': 'o'}

        # If we are not time based, we bail out!
        if not self.time_based:
            return None

        # Check if we are valid
        if status in small_states and small_states[status] not in self.escalation_options:
            return None

        # Look for the min of our future validity
        start = self.first_notification_time * interval + creation_time

        # If we are after the classic next time, we are not asking for a smaller interval
        if start > t_wished:
            return None

        # Maybe the time we found is not a valid one....
        if self.escalation_period is not None and not self.escalation_period.is_time_valid(start):
            return None

        # Ok so I ask for my start as a possibility for the next notification time
        return start


    # Check is required prop are set:
    # template are always correct
    # contacts OR contactgroups is need
    def is_correct(self):
        state = True
        cls = self.__class__

        # If we got the _time parameters, we are time based. Unless, we are not :)
        if hasattr(self, 'first_notification_time') or hasattr(self, 'last_notification_time'):
            self.time_based = True
            special_properties = _special_properties_time_based
        else:  # classic ones
            special_properties = _special_properties

        for prop, entry in cls.properties.items():
            if prop not in special_properties:
                if not hasattr(self, prop) and entry.required:
                    logger.info('%s: I do not have %s', self.get_name(), prop)
                    state = False  # Bad boy...

        # Raised all previously saw errors like unknown contacts and co
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                logger.info(err)

        # Ok now we manage special cases...
        if not hasattr(self, 'contacts') and not hasattr(self, 'contact_groups'):
            logger.info('%s: I do not have contacts nor contact_groups', self.get_name())
            state = False

        # If time_based or not, we do not check all properties
        if self.time_based:
            if not hasattr(self, 'first_notification_time'):
                logger.info('%s: I do not have first_notification_time', self.get_name())
                state = False
            if not hasattr(self, 'last_notification_time'):
                logger.info('%s: I do not have last_notification_time', self.get_name())
                state = False
        else:  # we check classical properties
            if not hasattr(self, 'first_notification'):
                logger.info('%s: I do not have first_notification', self.get_name())
                state = False
            if not hasattr(self, 'last_notification'):
                logger.info('%s: I do not have last_notification', self.get_name())
                state = False

        return state


class Escalations(Items):
    name_property = "escalation_name"
    inner_class = Escalation

    def linkify(self, timeperiods, contacts, services, hosts):
        self.linkify_with_timeperiods(timeperiods, 'escalation_period')
        self.linkify_with_contacts(contacts)
        self.linkify_es_by_s(services)
        self.linkify_es_by_h(hosts)

    def add_escalation(self, es):
        self.add_item(es)

    # Will register escalations into service.escalations
    def linkify_es_by_s(self, services):
        for es in self:
            # If no host, no hope of having a service
            if not (hasattr(es, 'host_name') and hasattr(es, 'service_description')):
                continue
            es_hname, sdesc = es.host_name, es.service_description
            if '' in (es_hname.strip(), sdesc.strip()):
                continue
            for hname in strip_and_uniq(es_hname.split(',')):
                if sdesc.strip() == '*':
                    slist = services.find_srvs_by_hostname(hname)
                    if slist is not None:
                        for s in slist:
                            s.escalations.append(es)
                else:
                    for sname in strip_and_uniq(sdesc.split(',')):
                        s = services.find_srv_by_name_and_hostname(hname, sname)
                        if s is not None:
                            # print "Linking service", s.get_name(), 'with me', es.get_name()
                            s.escalations.append(es)
                            # print "Now service", s.get_name(), 'have', s.escalations

    # Will register escalations into host.escalations
    def linkify_es_by_h(self, hosts):
        for es in self:
            # If no host, no hope of having a service
            if (not hasattr(es, 'host_name') or es.host_name.strip() == ''
                    or (hasattr(es, 'service_description')
                        and es.service_description.strip() != '')):
                continue
            # I must be NOT a escalation on for service
            for hname in strip_and_uniq(es.host_name.split(',')):
                h = hosts.find_by_name(hname)
                if h is not None:
                    # print "Linking host", h.get_name(), 'with me', es.get_name()
                    h.escalations.append(es)
                    # print "Now host", h.get_name(), 'have', h.escalations

    # We look for contacts property in contacts and
    def explode(self, hosts, hostgroups, contactgroups):
        for i in self:
            # items::explode_host_groups_into_hosts
            # take all hosts from our hostgroup_name into our host_name property
            self.explode_host_groups_into_hosts(i, hosts, hostgroups)

            # items::explode_contact_groups_into_contacts
            # take all contacts from our contact_groups into our contact property
            self.explode_contact_groups_into_contacts(i, contactgroups)
