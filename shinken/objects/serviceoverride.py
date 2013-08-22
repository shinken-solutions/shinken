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

""" This is the main class for the Serviceoverride object. It allows to
override specific service instances properties. This is mainly useful for
dynamycally generated services such as those linked to host templates (those
defined in packs for instances), or linked to hostgroups. This allows to
override a specific instance parameters without having to define a complete
new service.
"""

from item import Item, Items
from shinken.autoslots import AutoSlots
from shinken.util import to_list_of_names, to_name_if_possible
from shinken.property import BoolProp, IntegerProp, CharProp, StringProp, ListProp
from shinken.log import logger


class Serviceoverride(Item):
    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    id = 1  # zero is reserved for host (primary node for parents)
    my_type = 'serviceoverride'

    # properties defined by configuration
    # *required: is required in conf
    # *default: default value if no set in conf
    # *pythonize: function to call when transforming string to python object
    # *fill_brok: if set, send to broker. there are two categories: full_status for initial and update status, check_result for check results
    # *no_slots: do not take this property for __slots__
    #  Only for the initial call
    # conf_send_preparation: if set, will pass the property to this function. It's used to "flatten"
    #  some dangerous properties like realms that are too 'linked' to be send like that.
    # brok_transformation: if set, will call the function with the value of the property
    #  the major times it will be to flatten the data (like realm_name instead of the realm object).
    #
    # As the goal of a Serviceoverride instance is to define parameters that
    # have to be overriden on the corresonding Service instance, properties
    # are the same as Service class. Some are willingly forgotten (disabled)
    # because when they are applied on the Service instance, they have already
    # been processed by arbiter's previous phases, and linked to other objects
    # (mainly during explode phase).
    properties = Item.properties.copy()
    properties.update({
        'host_name':              StringProp(fill_brok=['full_status', 'check_result', 'next_schedule']),
        'hostgroup_name':         StringProp(default='', fill_brok=['full_status']),
        'service_description':    StringProp(fill_brok=['full_status', 'check_result', 'next_schedule']),
        'display_name':           StringProp(default='', fill_brok=['full_status']),
        #'servicegroups' have already been added members (services) during explode phase.
        'is_volatile':            BoolProp(default='0', fill_brok=['full_status']),
        'check_command':          StringProp(fill_brok=['full_status']),
        'initial_state':          CharProp(default='o', fill_brok=['full_status']),
        'max_check_attempts':     IntegerProp(fill_brok=['full_status']),
        'check_interval':         IntegerProp(fill_brok=['full_status']),
        'retry_interval':         IntegerProp(fill_brok=['full_status']),
        'active_checks_enabled':  BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'passive_checks_enabled': BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'check_period':           StringProp(brok_transformation=to_name_if_possible, fill_brok=['full_status']),
        'obsess_over_service':    BoolProp(default='0', fill_brok=['full_status'], retention=True),
        'check_freshness':        BoolProp(default='0', fill_brok=['full_status']),
        'freshness_threshold':    IntegerProp(default='0', fill_brok=['full_status']),
        'event_handler':          StringProp(default='', fill_brok=['full_status']),
        'event_handler_enabled':  BoolProp(default='0', fill_brok=['full_status'], retention=True),
        'low_flap_threshold':     IntegerProp(default='-1', fill_brok=['full_status']),
        'high_flap_threshold':    IntegerProp(default='-1', fill_brok=['full_status']),
        'flap_detection_enabled': BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'flap_detection_options': ListProp(default='o,w,c,u', fill_brok=['full_status']),
        'process_perf_data':      BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'retain_status_information': BoolProp(default='1', fill_brok=['full_status']),
        'retain_nonstatus_information': BoolProp(default='1', fill_brok=['full_status']),
        'notification_interval':  IntegerProp(default='60', fill_brok=['full_status']),
        'first_notification_delay': IntegerProp(default='0', fill_brok=['full_status']),
        'notification_period':    StringProp(brok_transformation=to_name_if_possible, fill_brok=['full_status']),
        'notification_options':   ListProp(default='w,u,c,r,f,s', fill_brok=['full_status']),
        'notifications_enabled':  BoolProp(default='1', fill_brok=['full_status'], retention=True),
        'contacts':               StringProp(default='', brok_transformation=to_list_of_names, fill_brok=['full_status']),
        'contact_groups':         StringProp(default='', fill_brok=['full_status']),
        'stalking_options':       ListProp(default='', fill_brok=['full_status']),
        'notes':                  StringProp(default='', fill_brok=['full_status']),
        'notes_url':              StringProp(default='', fill_brok=['full_status']),
        'action_url':             StringProp(default='', fill_brok=['full_status']),
        'icon_image':             StringProp(default='', fill_brok=['full_status']),
        'icon_image_alt':         StringProp(default='', fill_brok=['full_status']),
        'icon_set':               StringProp(default='', fill_brok=['full_status']),
        'failure_prediction_enabled': BoolProp(default='0', fill_brok=['full_status']),
        'parallelize_check':       BoolProp(default='1', fill_brok=['full_status']),

        # Shinken specific
        'poller_tag':              StringProp(default='None'),
        'reactionner_tag':         StringProp(default='None'),
        'resultmodulations':       StringProp(default=''),
        'business_impact_modulations':    StringProp(default=''),
        'escalations':             StringProp(default='', fill_brok=['full_status']),
        'maintenance_period':      StringProp(default='', brok_transformation=to_name_if_possible, fill_brok=['full_status']),
        'time_to_orphanage':       IntegerProp(default="300", fill_brok=['full_status']),
        'merge_host_contacts': 	   BoolProp(default='0', fill_brok=['full_status']),

        # Easy Service dep definition
        #'service_dependencies' have already been processed during explode phase.

        # service generator
        #'duplicate_foreach' have already been processed during explode phase.
        #'default_value' has no meaning here as we want to override default.

        # Business_Impact value
        'business_impact':         IntegerProp(default='2', fill_brok=['full_status']),

        # Load some triggers
        #'trigger' have already been processed during explode phase.

        # Trending
        'trending_policies':    ListProp(default='', fill_brok=['full_status']),

        # Our check ways. By defualt void, but will filled by an inner if need
        'checkmodulations':       ListProp(default='', fill_brok=['full_status']),
        'macromodulations':       ListProp(default=''),

        # Custom views
        'custom_views':           ListProp(default='', fill_brok=['full_status']),

        # UI aggregation
        'aggregation':            StringProp(default='', fill_brok=['full_status']),
    })

#######
#                   __ _                       _   _
#                  / _(_)                     | | (_)
#   ___ ___  _ __ | |_ _  __ _ _   _ _ __ __ _| |_ _  ___  _ __
#  / __/ _ \| '_ \|  _| |/ _` | | | | '__/ _` | __| |/ _ \| '_ \
# | (_| (_) | | | | | | | (_| | |_| | | | (_| | |_| | (_) | | | |
#  \___\___/|_| |_|_| |_|\__, |\__,_|_|  \__,_|\__|_|\___/|_| |_|
#                         __/ |
#                        |___/
######

    # Check is required prop are set:
    # host_name and service_description are needed
    def is_correct(self):
        state = hasattr(self, 'service_description') and hasattr(self, 'host_name')
        # Then look if we have some errors in the conf
        # Juts print warnings, but raise errors
        for err in self.configuration_warnings:
            logger.warning("[serviceoverride::%s] %s" % (self.get_name(), err))

        # Raised all previously saw errors like unknown contacts and co
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                logger.error("[serviceoverride::%s] %s" % (self.get_name(), err))
        return state

    # Give a nice name output
    def get_name(self):
        h = getattr(self, 'host_name', '[n/a]')
        s = getattr(self, 'service_description', '[n/a]')
        return "%s/%s" % (h, s)

    def get_full_name(self):
        return "%s/%s" % (self.host_name, self.service_description)


# Class for the serviceoverrides lists. It's mainly for configuration
# part
class Serviceoverrides(Items):
    inner_class = Serviceoverride  # use for know what is in items

    def remove_overrides(self):
        self.items.clear()

    def apply_overrides(self, services):
        for o in self:
            # Checks that object has the mandatory attributes set.
            err = None
            if not hasattr(o, "host_name"):
                err = "Error: service override has no host_name"
                o.configuration_errors.append(err)
            if not hasattr(o, "service_description"):
                err = "Error: service override has no service_description"
                o.configuration_errors.append(err)
            if err is not None:
                continue
            # We are forced to walk through services to find them as hosts and
            # services are not yet linked.
            svc = None
            for s in services:
                if not hasattr(s, "host_name") or not hasattr(s, "service_description"):
                    # this is a template
                    continue
                if s.host_name == o.host_name and s.service_description == o.service_description:
                    svc = s
                    break
            if svc is None:
                err = "Error: the service '%s' for host '%s' in service override is unknown" % (o.service_description, o.host_name)
                o.configuration_errors.append(err)
                continue
            for prop, entry in Serviceoverride.properties.items():
                # only overrides service properties exlpicitely set in
                # serviceoverride configuration.
                excludes = ['host_name', 'service_description', 'use']
                if hasattr(o, prop) and not prop in excludes:
                    val = getattr(o, prop)
                    setattr(svc, prop, val)
