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

import time

from item import Item, Items
from shinken.property import StringProp
from shinken.util import to_name_if_possible
from shinken.log import logger


class MacroModulation(Item):
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'macromodulation'

    properties = Item.properties.copy()
    properties.update({
        'macromodulation_name': StringProp(fill_brok=['full_status']),
        'modulation_period': StringProp(brok_transformation=to_name_if_possible,
                                        fill_brok=['full_status']),
    })

    running_properties = Item.running_properties.copy()

    _special_properties = ('modulation_period',)

    macros = {}

    # For debugging purpose only (nice name)
    def get_name(self):
        return self.macromodulation_name

    # Will say if we are active or not
    def is_active(self):
        now = int(time.time())
        if not self.modulation_period or self.modulation_period.is_time_valid(now):
            return True
        return False

    # Should have all properties, or a void macro_period
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
                    logger.warning(
                        "[macromodulation::%s] %s property not set", self.get_name(), prop
                    )
                    state = False  # Bad boy...

        # Ok just put None as modulation_period, means 24x7
        if not hasattr(self, 'modulation_period'):
            self.modulation_period = None

        return state


class MacroModulations(Items):
    name_property = "macromodulation_name"
    inner_class = MacroModulation

    def linkify(self, timeperiods):
        self.linkify_with_timeperiods(timeperiods, 'modulation_period')
