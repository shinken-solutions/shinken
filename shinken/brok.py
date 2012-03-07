#!/usr/bin/env python

# Copyright (C) 2009-2011 :
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


class Brok:
    """A Brok is a piece of information exported by Shinken to the Broker.
    Broker can do whatever he wants with it.
    """
    __slots__ = ('__dict__', 'id', 'type', 'data')
    id = 0
    my_type = 'brok'

    def __init__(self, type, data):
        self.type = type
        self.id = self.__class__.id
        self.__class__.id += 1
        self.data = data

    def __str__(self):
        return str(self.__dict__) + '\n'
