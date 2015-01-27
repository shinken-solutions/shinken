#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2014:
#     Gabes Jean, naparuba@gmail.com
#     Gerhard Lausser, Gerhard.Lausser@consol.de
#     Gregory Starck, g.starck@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
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

from action import Action
from shinken.property import IntegerProp, StringProp, FloatProp, BoolProp
from shinken.autoslots import AutoSlots

""" TODO: Add some comment about this class for the doc"""
class EventHandler(Action):
    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    my_type = 'eventhandler'

    properties = {
        'is_a':           StringProp(default='eventhandler'),
        'type':           StringProp(default=''),
        '_in_timeout':    StringProp(default=False),
        'status':         StringProp(default=''),
        'exit_status':    StringProp(default=3),
        'output':         StringProp(default=''),
        'long_output':    StringProp(default=''),
        't_to_go':        StringProp(default=0),
        'check_time':     StringProp(default=0),
        'execution_time': FloatProp(default=0),
        'u_time':         FloatProp(default=0.0),
        's_time':         FloatProp(default=0.0),
        'env':            StringProp(default={}),
        'perf_data':      StringProp(default=''),
        'sched_id':       IntegerProp(default=0),
        'timeout':        IntegerProp(default=10),
        'check_time':     IntegerProp(default=0),
        'command':        StringProp(default=''),
        'module_type':    StringProp(default='fork'),
        'worker':         StringProp(default='none'),
        'reactionner_tag':     StringProp(default='None'),
        'is_snapshot':    BoolProp(default=False),
    }

    # id = 0  #Is common to Actions
    def __init__(self, command, id=None, ref=None, timeout=10, env={},
                 module_type='fork', reactionner_tag='None', is_snapshot=False):
        self.is_a = 'eventhandler'
        self.type = ''
        self.status = 'scheduled'
        if id is None:  # id != None is for copy call only
            self.id = Action.id
            Action.id += 1
        self.ref = ref
        self._in_timeout = False
        self.timeout = timeout
        self.exit_status = 3
        self.command = command
        self.output = ''
        self.long_output = ''
        self.t_to_go = time.time()
        self.check_time = 0
        self.execution_time = 0
        self.u_time = 0
        self.s_time = 0
        self.perf_data = ''
        self.env = {}
        self.module_type = module_type
        self.worker = 'none'
        self.reactionner_tag = reactionner_tag
        self.is_snapshot = is_snapshot


    # return a copy of the check but just what is important for execution
    # So we remove the ref and all
    def copy_shell(self):
        # We create a dummy check with nothing in it, just defaults values
        return self.copy_shell__(EventHandler('', id=self.id, is_snapshot=self.is_snapshot))


    def get_return_from(self, e):
        self.exit_status = e.exit_status
        self.output = e.output
        self.long_output = getattr(e, 'long_output', '')
        self.check_time = e.check_time
        self.execution_time = getattr(e, 'execution_time', 0.0)
        self.perf_data = getattr(e, 'perf_data', '')


    def get_outputs(self, out, max_plugins_output_length):
        self.output = out


    def is_launchable(self, t):
        return t >= self.t_to_go


    def __str__(self):
        return "Check %d status:%s command:%s" % (self.id, self.status, self.command)


    def get_id(self):
        return self.id


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


    # Inverted function of getstate
    def __setstate__(self, state):
        cls = self.__class__
        self.id = state['id']
        for prop in cls.properties:
            if prop in state:
                setattr(self, prop, state[prop])
        if not hasattr(self, 'worker'):
            self.worker = 'none'
        if not getattr(self, 'module_type', None):
            self.module_type = 'fork'
        # s_time and u_time are added between 1.2 and 1.4
        if not hasattr(self, 'u_time'):
            self.u_time = 0
            self.s_time = 0
