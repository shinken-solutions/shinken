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

import time

""" TODO: Add some comment about this class for the doc"""
class Comment:
    id = 1

    properties = {
        'entry_time':   None,
        'persistent':   None,
        'author':       None,
        'comment':      None,
        'comment_type': None,
        'entry_type':   None,
        'source':       None,
        'expires':      None,
        'expire_time':  None,
        'can_be_deleted': None,

        # TODO: find a very good way to handle the downtime "ref".
        # ref must effectively not be in properties because it points
        # onto a real object.
        # 'ref':  None
    }

    # Adds a comment to a particular service. If the "persistent" field
    # is set to zero (0), the comment will be deleted the next time
    # Shinken is restarted. Otherwise, the comment will persist
    # across program restarts until it is deleted manually.
    def __init__(self, ref, persistent, author, comment, comment_type, entry_type, source, expires,
                 expire_time):
        self.id = self.__class__.id
        self.__class__.id += 1
        self.ref = ref  # pointer to srv or host we are apply
        self.entry_time = int(time.time())
        self.persistent = persistent
        self.author = author
        self.comment = comment
        # Now the hidden attributes
        # HOST_COMMENT=1,SERVICE_COMMENT=2
        self.comment_type = comment_type
        # USER_COMMENT=1,DOWNTIME_COMMENT=2,FLAPPING_COMMENT=3,ACKNOWLEDGEMENT_COMMENT=4
        self.entry_type = entry_type
        # COMMENTSOURCE_INTERNAL=0,COMMENTSOURCE_EXTERNAL=1
        self.source = source
        self.expires = expires
        self.expire_time = expire_time
        self.can_be_deleted = False

    def __str__(self):
        return "Comment id=%d %s" % (self.id, self.comment)

    # Call by pickle for dataify the ackn
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

        # Maybe it's not a dict but a list like in the old 0.4 format
        # so we should call the 0.4 function for it
        if isinstance(state, list):
            self.__setstate_deprecated__(state)
            return

        self.id = state['id']
        for prop in cls.properties:
            if prop in state:
                setattr(self, prop, state[prop])

        # to prevent from duplicating id in comments:
        if self.id >= cls.id:
            cls.id = self.id + 1

    # This function is DEPRECATED and will be removed in a future version of
    # Shinken. It should not be useful any more after a first load/save pass.
    # Inverted function of getstate
    def __setstate_deprecated__(self, state):
        cls = self.__class__
        # Check if the len of this state is like the previous,
        # if not, we will do errors!
        # -1 because of the 'id' prop
        if len(cls.properties) != (len(state) - 1):
            self.debug("Passing comment")
            return

        self.id = state.pop()
        for prop in cls.properties:
            val = state.pop()
            setattr(self, prop, val)
        if self.id >= cls.id:
            cls.id = self.id + 1
