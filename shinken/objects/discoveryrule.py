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

from copy import copy

from item import Item, Items
from shinken.objects.matchingitem import MatchingItem
from service import Service
from host import Host
from shinken.property import StringProp, ListProp, IntegerProp


class Discoveryrule(MatchingItem):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'discoveryrule'

    properties = Item.properties.copy()
    properties.update({
        'discoveryrule_name':    StringProp(),
        'creation_type':         StringProp(default='service'),
        'discoveryrule_order':   IntegerProp(default=0),
        # 'check_command':         StringProp (),
        # 'service_description':   StringProp (),
        # 'use':                   StringProp(),
    })

    running_properties = {
        'configuration_warnings':   ListProp(default=[]),
        'configuration_errors': ListProp(default=[]),
    }

    macros = {}

    # The init of a discovery will set the property of
    # Discoveryrule.properties as in setattr, but all others
    # will be in a list because we need to have all names
    # and not lost all in __dict__
    def __init__(self, params={}):
        cls = self.__class__

        # We have our own id of My Class type :)
        # use set attr for going into the slots
        # instead of __dict__ :)
        setattr(self, 'id', cls.id)
        cls.id += 1

        self.matches = {}  # for matching rules
        self.not_matches = {}  # for rules that should NOT match
        self.writing_properties = {}

        for key in params:
            # delistify attributes if there is only one value
            params[key] = self.compact_unique_attr_value(params[key])

        # Get the properties of the Class we want
        if 'creation_type' not in params:
            params['creation_type'] = 'service'

        map = {'service': Service, 'host': Host}
        t = params['creation_type']
        if t not in map:
            return
        tcls = map[t]

        # In my own property:
        #  -> in __dict__
        # In the properties of the 'creation_type' Class:
        #  -> in self.writing_properties
        # if not, in matches or not match (if key starts
        # with a !, it's a not rule)
        # -> in self.matches or self.not_matches
        # in writing properties if start with + (means 'add this')
        # in writing properties if start with - (means 'del this')
        for key in params:
            # Some key are quite special
            if key in cls.properties:
                setattr(self, key, params[key])
            elif (key in ['use'] or
                  key.startswith('+') or
                  key.startswith('-') or
                  key in tcls.properties or
                  key.startswith('_')):
                self.writing_properties[key] = params[key]
            else:
                if key.startswith('!'):
                    key = key.split('!')[1]
                    self.not_matches[key] = params['!' + key]
                else:
                    self.matches[key] = params[key]

        # Then running prop :)
        cls = self.__class__
        # adding running properties like latency, dependency list, etc
        for prop, entry in cls.running_properties.items():
            # Copy is slow, so we check type
            # Type with __iter__ are list or dict, or tuple.
            # Item need it's own list, so qe copy
            val = entry.default
            if hasattr(val, '__iter__'):
                setattr(self, prop, copy(val))
            else:
                setattr(self, prop, val)

            # each instance to have his own running prop!


    # Output name
    def get_name(self):
        try:
            return self.discoveryrule_name
        except AttributeError:
            return "UnnamedDiscoveryRule"


class Discoveryrules(Items):
    name_property = "discoveryrule_name"
    inner_class = Discoveryrule
