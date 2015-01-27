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
from shinken.property import StringProp
from shinken.util import to_name_if_possible
from shinken.log import logger


class CheckModulation(Item):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'checkmodulation'

    properties = Item.properties.copy()
    properties.update({
        'checkmodulation_name':
            StringProp(fill_brok=['full_status']),
        'check_command':
            StringProp(fill_brok=['full_status']),
        'check_period':
            StringProp(brok_transformation=to_name_if_possible, fill_brok=['full_status']),
    })

    running_properties = Item.running_properties.copy()

    _special_properties = ('check_period',)

    macros = {}

    # For debugging purpose only (nice name)
    def get_name(self):
        return self.checkmodulation_name


    # Will look at if our check_period is ok, and give our check_command if we got it
    def get_check_command(self, t_to_go):
        if not self.check_period or self.check_period.is_time_valid(t_to_go):
            return self.check_command
        return None


    # Should have all properties, or a void check_period
    def is_correct(self):
        state = True
        cls = self.__class__

        # Raised all previously saw errors like unknown commands or timeperiods
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                logger.error("[item::%s] %s", self.get_name(), err)

        for prop, entry in cls.properties.items():
            if prop not in cls._special_properties:
                if not hasattr(self, prop) and entry.required:
                    logger.warning("[checkmodulation::%s] %s property not set",
                                   self.get_name(), prop)
                    state = False  # Bad boy...

        # Ok now we manage special cases...
        # Service part
        if not hasattr(self, 'check_command'):
            logger.warning("[checkmodulation::%s] do not have any check_command defined",
                           self.get_name())
            state = False
        else:
            if self.check_command is None:
                logger.warning("[checkmodulation::%s] a check_command is missing", self.get_name())
                state = False
            if not self.check_command.is_valid():
                logger.warning("[checkmodulation::%s] a check_command is invalid", self.get_name())
                state = False

        # Ok just put None as check_period, means 24x7
        if not hasattr(self, 'check_period'):
            self.check_period = None

        return state


    # In the scheduler we need to relink the commandCall with
    # the real commands
    def late_linkify_cw_by_commands(self, commands):
        if self.check_command:
            self.check_command.late_linkify_with_command(commands)


class CheckModulations(Items):
    name_property = "checkmodulation_name"
    inner_class = CheckModulation


    def linkify(self, timeperiods, commands):
        self.linkify_with_timeperiods(timeperiods, 'check_period')
        self.linkify_one_command_with_commands(commands, 'check_command')


    def new_inner_member(self, name=None, params={}):
        if name is None:
            name = CheckModulation.id
        params['checkmodulation_name'] = name
        # print "Asking a new inner checkmodulation from name %s with params %s" % (name, params)
        cw = CheckModulation(params)
        self.add_item(cw)
