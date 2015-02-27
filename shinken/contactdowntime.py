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
from shinken.log import logger

""" TODO: Add some comment about this class for the doc"""
class ContactDowntime:
    id = 1

    # Just to list the properties we will send as pickle
    # so to others daemons, so all but NOT REF
    properties = {
        # 'activate_me':  None,
        # 'entry_time':   None,
        # 'fixed':        None,
        'start_time':   None,
        # 'duration':     None,
        # 'trigger_id':   None,
        'end_time':     None,
        # 'real_end_time': None,
        'author':       None,
        'comment':      None,
        'is_in_effect': None,
        # 'has_been_triggered': None,
        'can_be_deleted': None,
    }

    # Schedule a contact downtime. It's far more easy than a host/service
    # one because we got a beginning, and an end. That's all for running.
    # got also an author and a comment for logging purpose.
    def __init__(self, ref, start_time, end_time, author, comment):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.ref = ref  # pointer to srv or host we are apply
        self.start_time = start_time
        self.end_time = end_time
        self.author = author
        self.comment = comment
        self.is_in_effect = False
        self.can_be_deleted = False
        # self.add_automatic_comment()


    # Check if we came into the activation of this downtime
    def check_activation(self):
        now = time.time()
        was_is_in_effect = self.is_in_effect
        self.is_in_effect = (self.start_time <= now <= self.end_time)
        logger.info("CHECK ACTIVATION:%s", self.is_in_effect)

        # Raise a log entry when we get in the downtime
        if not was_is_in_effect and self.is_in_effect:
            self.enter()

        # Same for exit purpose
        if was_is_in_effect and not self.is_in_effect:
            self.exit()

    def in_scheduled_downtime(self):
        return self.is_in_effect

    # The referenced host/service object enters now a (or another) scheduled
    # downtime. Write a log message only if it was not already in a downtime
    def enter(self):
        self.ref.raise_enter_downtime_log_entry()

    # The end of the downtime was reached.
    def exit(self):
        self.ref.raise_exit_downtime_log_entry()
        self.can_be_deleted = True

    # A scheduled downtime was prematurely canceled
    def cancel(self):
        self.is_in_effect = False
        self.ref.raise_cancel_downtime_log_entry()
        self.can_be_deleted = True

    # Call by pickle to dataify the comment
    # because we DO NOT WANT REF in this pickleisation!
    def __getstate__(self):
        # print "Asking a getstate for a downtime on", self.ref.get_dbg_name()
        cls = self.__class__
        # id is not in *_properties
        res = [self.id]
        for prop in cls.properties:
            res.append(getattr(self, prop))
        # We reverse because we want to recreate
        # By check at properties in the same order
        res.reverse()
        return res

    # Inverted function of getstate
    def __setstate__(self, state):
        cls = self.__class__
        self.id = state.pop()
        for prop in cls.properties:
            val = state.pop()
            setattr(self, prop, val)
        if self.id >= cls.id:
            cls.id = self.id + 1
