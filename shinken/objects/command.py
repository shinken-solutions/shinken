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
from shinken.brok import Brok
from shinken.property import StringProp, IntegerProp, BoolProp
from shinken.autoslots import AutoSlots


# Ok, slots are fun: you cannot set the __autoslots__
# on the same class you use, fun isn't it? So we define*
# a dummy useless class to get such :)
class DummyCommand(object):
    pass


class Command(Item):
    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    id = 0
    my_type = "command"

    properties = Item.properties.copy()
    properties.update({
        'command_name': StringProp(fill_brok=['full_status']),
        'command_line': StringProp(fill_brok=['full_status']),
        'poller_tag':   StringProp(default='None'),
        'reactionner_tag':   StringProp(default='None'),
        'module_type':  StringProp(default=None),
        'timeout':      IntegerProp(default=-1),
        'enable_environment_macros': BoolProp(default=False),
    })

    def __init__(self, params={}):
        setattr(self, 'id', self.__class__.id)
        # self.id = self.__class__.id
        self.__class__.id += 1

        self.init_running_properties()

        self.customs = {}

        for key in params:
            # delistify attributes if there is only one value
            params[key] = self.compact_unique_attr_value(params[key])
            # Manage customs values
            if key.startswith('_'):
                self.customs[key.upper()] = params[key]
            else:
                setattr(self, key, params[key])

        if not hasattr(self, 'timeout'):
            self.timeout = '-1'

        if not hasattr(self, 'poller_tag'):
            self.poller_tag = 'None'
        if not hasattr(self, 'enable_environment_macros'):
            self.enable_environment_macros = 0
        if not hasattr(self, 'reactionner_tag'):
            self.reactionner_tag = 'None'
        if not hasattr(self, 'module_type'):
            # If the command start with a _, set the module_type
            # as the name of the command, without the _
            if getattr(self, 'command_line', '').startswith('_'):
                module_type = getattr(self, 'command_line', '').split(' ')[0]
                # and we remove the first _
                self.module_type = module_type[1:]
            # If no command starting with _, be fork :)
            else:
                self.module_type = 'fork'

    def get_name(self):
        return self.command_name

    def __str__(self):
        return str(self.__dict__)

    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        # Now config properties
        for prop, entry in cls.properties.items():
            # Is this property intended for broking?
            # if 'fill_brok' in entry[prop]:
            if brok_type in entry.fill_brok:
                if hasattr(self, prop):
                    data[prop] = getattr(self, prop)
                # elif 'default' in entry[prop]:
                #    data[prop] = entry.default


    # Call by pickle to dataify the comment
    # because we DO NOT WANT REF in this pickleisation!
    def __getstate__(self):
        cls = self.__class__
        # id is not in *_properties
        res = {'id': self.id}
        for prop in cls.properties:
            if hasattr(self, prop):
                res[prop] = getattr(self, prop)

        return res

    # Inversed function of getstate
    def __setstate__(self, state):
        cls = self.__class__
        # We move during 1.0 to a dict state
        # but retention file from 0.8 was tuple
        if isinstance(state, tuple):
            self.__setstate_pre_1_0__(state)
            return
        self.id = state['id']
        for prop in cls.properties:
            if prop in state:
                setattr(self, prop, state[prop])

    # In 1.0 we move to a dict save. Before, it was
    # a tuple save, like
    # ({'id': 11}, {'poller_tag': 'None', 'reactionner_tag': 'None',
    # 'command_line': u'/usr/local/nagios/bin/rss-multiuser',
    # 'module_type': 'fork', 'command_name': u'notify-by-rss'})
    def __setstate_pre_1_0__(self, state):
        for d in state:
            for k, v in d.items():
                setattr(self, k, v)


class Commands(Items):

    inner_class = Command
    name_property = "command_name"
