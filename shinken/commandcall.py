#!/usr/bin/env python
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

from shinken.autoslots import AutoSlots
from shinken.property import StringProp, BoolProp, IntegerProp


class DummyCommandCall(object):
    """Ok, slots are fun: you cannot set the __autoslots__
     on the same class you use, fun isn't it? So we define*
     a dummy useless class to get such :)
    """
    pass


class CommandCall(DummyCommandCall):
    """This class is use when a service, contact or host define
    a command with args.
    """
    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    # __slots__ = ('id', 'call', 'command', 'valid', 'args', 'poller_tag',
    #              'reactionner_tag', 'module_type', '__dict__')
    id = 0
    my_type = 'CommandCall'

    properties = {
        'call':            StringProp(),
        'command':         StringProp(),
        'poller_tag':      StringProp(default='None'),
        'reactionner_tag': StringProp(default='None'),
        'module_type':     StringProp(default='fork'),
        'valid':           BoolProp(default=False),
        'args':            StringProp(default=[]),
        'timeout':         IntegerProp(default=-1),
        'late_relink_done': BoolProp(default=False),
        'enable_environment_macros': BoolProp(default=False),
    }

    def __init__(self, commands, call, poller_tag='None',
                 reactionner_tag='None', enable_environment_macros=0):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.call = call
        self.timeout = -1
        # Now split by ! and get command and args
        self.get_command_and_args()
        self.command = commands.find_by_name(self.command.strip())
        self.late_relink_done = False  # To do not relink again and again the same commandcall
        if self.command is not None:
            self.valid = True
        else:
            self.valid = False
        if self.valid:
            # If the host/service do not give an override poller_tag, take
            # the one of the command
            self.poller_tag = poller_tag  # from host/service
            self.reactionner_tag = reactionner_tag
            self.module_type = self.command.module_type
            self.enable_environment_macros = self.command.enable_environment_macros
            self.timeout = int(self.command.timeout)
            if self.valid and poller_tag is 'None':
                # from command if not set
                self.poller_tag = self.command.poller_tag
            # Same for reactionner tag
            if self.valid and reactionner_tag is 'None':
                # from command if not set
                self.reactionner_tag = self.command.reactionner_tag

    def get_command_and_args(self):
        """We want to get the command and the args with ! splitting.
        but don't forget to protect against the \! to do not split them
        """

        # First protect
        p_call = self.call.replace('\!', '___PROTECT_EXCLAMATION___')
        tab = p_call.split('!')
        self.command = tab[0]
        # Reverse the protection
        self.args = [s.replace('___PROTECT_EXCLAMATION___', '!')
                     for s in tab[1:]]

    # If we didn't already lately relink us, do it
    def late_linkify_with_command(self, commands):
        if self.late_relink_done:
            return
        self.late_relink_done = True
        c = commands.find_by_name(self.command)
        self.command = c

    def is_valid(self):
        return self.valid

    def __str__(self):
        return str(self.__dict__)

    def get_name(self):
        return self.call

    def __getstate__(self):
        """Call by pickle to dataify the comment
        because we DO NOT WANT REF in this pickleisation!
        """
        cls = self.__class__
        # id is not in *_properties
        res = {'id': self.id}

        for prop in cls.properties:
            if hasattr(self, prop):
                res[prop] = getattr(self, prop)

        # The command is a bit special, we just put it's name
        # or a '' if need
        if self.command and not isinstance(self.command, basestring):
            res['command'] = self.command.get_name()
        # Maybe it's a repickle of a unpickle thing... (like with deepcopy). If so
        # only take the value
        elif self.command and isinstance(self.command, basestring):
            res['command'] = self.command
        else:
            res['command'] = ''

        return res

    def __setstate__(self, state):
        """Inverted function of getstate"""
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

    def __setstate_pre_1_0__(self, state):
        """In 1.0 we move to a dict save. Before, it was
        a tuple save, like
        ({'id': 11}, {'poller_tag': 'None', 'reactionner_tag': 'None',
        'command_line': u'/usr/local/nagios/bin/rss-multiuser',
        'module_type': 'fork', 'command_name': u'notify-by-rss'})
        """
        for d in state:
            for k, v in d.items():
                setattr(self, k, v)
