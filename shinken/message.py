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


class Message:
    """This is a simple message class for communications between actionners and
    workers

    """

    my_type = 'message'
    _type = None
    _data = None
    _from = None

    def __init__(self, id, type, data=None, source=None):
        self._type = type
        self._data = data
        self._from = id
        self.source = source

    def get_type(self):
        return self._type

    def get_data(self):
        return self._data

    def get_from(self):
        return self._from

    def str(self):
        return "Message from %d (%s), Type: %s Data: %s" % (
            self._from, self.source, self._type, self._data)
