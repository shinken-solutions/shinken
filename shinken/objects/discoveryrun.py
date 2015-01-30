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
from shinken.property import StringProp
from shinken.eventhandler import EventHandler
from shinken.macroresolver import MacroResolver


class Discoveryrun(MatchingItem):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'discoveryrun'

    properties = Item.properties.copy()
    properties.update({
        'discoveryrun_name': StringProp(),
        'discoveryrun_command': StringProp(),
    })

    running_properties = Item.running_properties.copy()
    running_properties.update({
        'current_launch': StringProp(default=None),
    })

    # The init of a discovery will set the property of
    # Discoveryrun.properties as in setattr, but all others
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

        # In my own property:
        #  -> in __dict__
        # if not, in matches or not match (if key starts
        # with a !, it's a not rule)
        # -> in self.matches or self.not_matches
        # in writing properties if start with + (means 'add this')
        for key in params:
            # delistify attributes if there is only one value
            params[key] = self.compact_unique_attr_value(params[key])
            if key in cls.properties:
                setattr(self, key, params[key])
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
            return self.discoveryrun_name
        except AttributeError:
            return "UnnamedDiscoveryRun"

    # A Run that is first level means that it do not have
    # any matching filter
    def is_first_level(self):
        return len(self.not_matches) + len(self.matches) == 0

    # Get an eventhandler object and launch it
    def launch(self, ctx=[], timeout=300):
        m = MacroResolver()
        cmd = m.resolve_command(self.discoveryrun_command, ctx)
        self.current_launch = EventHandler(cmd, timeout=timeout)
        self.current_launch.execute()

    def check_finished(self):
        max_output = 10 ** 9
        # print "Max output", max_output
        self.current_launch.check_finished(max_output)

    # Look if the current launch is done or not
    def is_finished(self):
        if self.current_launch is None:
            return True
        if self.current_launch.status in ('done', 'timeout'):
            return True
        return False

    # we use an EventHandler object, so we have output with a single line
    # and longoutput with the rest. We just need to return all
    def get_output(self):
        return '\n'.join([self.current_launch.output, self.current_launch.long_output])


class Discoveryruns(Items):
    name_property = "discoveryrun_name"
    inner_class = Discoveryrun

    def linkify(self, commands):
        for r in self:
            r.linkify_one_command_with_commands(commands, 'discoveryrun_command')
