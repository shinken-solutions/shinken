#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

from __future__ import absolute_import, division, print_function, unicode_literals

import six
from shinken.safepickle import SafeUnpickler
if six.PY2:
    import cPickle as pickle
else:
    import pickle
import sys
import io

class Brok(object):
    """A Brok is a piece of information exported by Shinken to the Broker.
    Broker can do whatever he wants with it.
    """
    #__slots__ = ('id', 'type', 'data', 'prepared', 'instance_id')
    id = 0
    my_type = 'brok'

    def __init__(self, _type, data):
        self.type = _type
        self.id = self.__class__.id
        self.__class__.id += 1
        self.data = pickle.dumps(data, pickle.HIGHEST_PROTOCOL)
        self.prepared = False


    def __str__(self):
        return str(self.__dict__)


    # We unserialize the data, and if some prop were
    # add after the serialize pass, we integer them in the data
    def prepare(self):
        # Maybe the brok is a old daemon one or was already prepared
        # if so, the data is already ok
        if not self.prepared:
            self.data = SafeUnpickler(io.BytesIO(self.data)).load()
            if hasattr(self, 'instance_id'):
                self.data['instance_id'] = self.instance_id
        self.prepared = True

#    # Call by pickle for dataify the ackn
#    # because we DO NOT WANT REF in this pickleisation!
#    def __getstate__(self):
#        # id is not in *_properties
#        res = {'id': self.id}
#        for prop in ("data", "instance_id", "prepared", "type"):
#            if hasattr(self, prop):
#                res[prop] = getattr(self, prop)
#        return res
#
#    # Inverted function of getstate
#    def __setstate__(self, state):
#        cls = self.__class__
#
#        for prop in ("id", "data", "instance_id", "prepared", "type"):
#            if prop in state:
#                setattr(self, prop, state[prop])
#
#        # to prevent from duplicating id in comments:
#        if self.id >= cls.id:
#            cls.id = self.id + 1
