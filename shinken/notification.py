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

from shinken.action import Action
from shinken.brok import Brok
from shinken.property import BoolProp, IntegerProp, StringProp, FloatProp
from shinken.autoslots import AutoSlots


class Notification(Action):
    """Please Add a Docstring to describe the class here"""

    # AutoSlots create the __slots__ with properties and
    # running_properties names
    __metaclass__ = AutoSlots

    my_type = 'notification'

    properties = {
        'is_a':                StringProp(default='notification'),
        'type':                StringProp(default=''),
        'notification_type':   IntegerProp(default=0, fill_brok=['full_status']),
        'start_time':          StringProp(default=0, fill_brok=['full_status']),
        'end_time':            StringProp(default=0, fill_brok=['full_status']),
        'contact_name':        StringProp(default='', fill_brok=['full_status']),
        'host_name':           StringProp(default='', fill_brok=['full_status']),
        'service_description': StringProp(default='', fill_brok=['full_status']),
        'reason_type':         StringProp(default=0, fill_brok=['full_status']),
        'state':               StringProp(default=0, fill_brok=['full_status']),
        'output':              StringProp(default='', fill_brok=['full_status']),
        'ack_author':          StringProp(default='', fill_brok=['full_status']),
        'ack_data':            StringProp(default='', fill_brok=['full_status']),
        'escalated':           BoolProp(default=False, fill_brok=['full_status']),
        'contacts_notified':   StringProp(default=0, fill_brok=['full_status']),
        'env':                 StringProp(default={}),
        'exit_status':         IntegerProp(default=3),
        'command_call':        StringProp(default=None),
        'execution_time':      FloatProp(default=0),
        'u_time':              FloatProp(default=0.0),
        's_time':              FloatProp(default=0.0),
        'contact':             StringProp(default=None),
        '_in_timeout':         BoolProp(default=False),
        'notif_nb':            IntegerProp(default=0),
        'status':              StringProp(default='scheduled'),
        't_to_go':             IntegerProp(default=0),
        'command':             StringProp(default=''),
        'sched_id':            IntegerProp(default=0),
        'timeout':             IntegerProp(default=10),
        'check_time':          IntegerProp(default=0),
        'module_type':         StringProp(default='fork', fill_brok=['full_status']),
        'worker':              StringProp(default='none'),
        'reactionner_tag':     StringProp(default='None'),
        'creation_time':       IntegerProp(default=0),
        'enable_environment_macros': BoolProp(default=False),
        # Keep a list of currently active escalations
        'already_start_escalations':  StringProp(default=set()),

    }

    macros = {
        'NOTIFICATIONTYPE':         'type',
        'NOTIFICATIONRECIPIENTS':   'recipients',
        'NOTIFICATIONISESCALATED':  'escalated',
        'NOTIFICATIONAUTHOR':       'author',
        'NOTIFICATIONAUTHORNAME':   'author_name',
        'NOTIFICATIONAUTHORALIAS':  'author_alias',
        'NOTIFICATIONCOMMENT':      'comment',
        'HOSTNOTIFICATIONNUMBER':   'notif_nb',
        'HOSTNOTIFICATIONID':       'id',
        'SERVICENOTIFICATIONNUMBER': 'notif_nb',
        'SERVICENOTIFICATIONID':    'id'
    }

    def __init__(self, type='PROBLEM', status='scheduled', command='UNSET',
                 command_call=None, ref=None, contact=None, t_to_go=0,
                 contact_name='', host_name='', service_description='',
                 reason_type=1, state=0, ack_author='', ack_data='',
                 escalated=False, contacts_notified=0,
                 start_time=0, end_time=0, notification_type=0, id=None,
                 notif_nb=1, timeout=10, env={}, module_type='fork',
                 reactionner_tag='None', enable_environment_macros=0):

        self.is_a = 'notification'
        self.type = type
        if id is None:  # id != None is for copy call only
            self.id = Action.id
            Action.id += 1
        self._in_timeout = False
        self.timeout = timeout
        self.status = status
        self.exit_status = 3
        self.command = command
        self.command_call = command_call
        self.output = None
        self.execution_time = 0
        self.u_time = 0  # user executon time
        self.s_time = 0  # system execution time

        self.ref = ref

        # Set host_name and description from the ref
        try:
            self.host_name = self.ref.host_name
        except Exception:
            self.host_name = host_name
        try:
            self.service_description = self.ref.service_description
        except Exception:
            self.service_description = service_description

        self.env = env
        self.module_type = module_type
        self.t_to_go = t_to_go
        self.notif_nb = notif_nb
        self.contact = contact

        # For brok part
        self.contact_name = contact_name
        self.reason_type = reason_type
        self.state = state
        self.ack_author = ack_author
        self.ack_data = ack_data
        self.escalated = escalated
        self.contacts_notified = contacts_notified
        self.start_time = start_time
        self.end_time = end_time
        self.notification_type = notification_type

        self.creation_time = time.time()
        self.worker = 'none'
        self.reactionner_tag = reactionner_tag
        self.already_start_escalations = set()
        self.enable_environment_macros = enable_environment_macros

    # return a copy of the check but just what is important for execution
    # So we remove the ref and all
    def copy_shell(self):
        # We create a dummy check with nothing in it, just defaults values
        return self.copy_shell__(Notification('', '', '', '', '', '', '', id=self.id))


    def is_launchable(self, t):
        return t >= self.t_to_go


    def is_administrative(self):
        if self.type in ('PROBLEM', 'RECOVERY'):
            return False
        else:
            return True


    def __str__(self):
        return "Notification %d status:%s command:%s ref:%s t_to_go:%s" % \
               (self.id, self.status, self.command, getattr(self, 'ref', 'unknown'),
                time.asctime(time.localtime(self.t_to_go)))


    def get_id(self):
        return self.id


    def get_return_from(self, n):
        self.exit_status = n.exit_status
        self.execution_time = n.execution_time


    # Fill data with info of item by looking at brok_type
    # in props of properties or running_properties
    def fill_data_brok_from(self, data, brok_type):
        cls = self.__class__
        # Now config properties
        for prop, entry in cls.properties.items():
            if brok_type in entry.fill_brok:
                data[prop] = getattr(self, prop)


    # Get a brok with initial status
    def get_initial_status_brok(self):
        data = {'id': self.id}

        self.fill_data_brok_from(data, 'full_status')
        b = Brok('notification_raise', data)
        return b


    # Call by pickle for dataify the comment
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
        # Hook for load of 0.4 notification: there were no
        # creation time, must put one
        if not hasattr(self, 'creation_time'):
            self.creation_time = time.time()
        if not hasattr(self, 'reactionner_tag'):
            self.reactionner_tag = 'None'
        if not hasattr(self, 'worker'):
            self.worker = 'none'
        if not getattr(self, 'module_type', None):
            self.module_type = 'fork'
        if not hasattr(self, 'already_start_escalations'):
            self.already_start_escalations = set()
        if not hasattr(self, 'execution_time'):
            self.execution_time = 0
        # s_time and u_time are added between 1.2 and 1.4
        if not hasattr(self, 'u_time'):
            self.u_time = 0
            self.s_time = 0
