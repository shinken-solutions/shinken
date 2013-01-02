#!/usr/bin/python

# -*- coding: utf-8 -*-

# Copyright (C) 2009-2012:
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

"""This Class is an helper for al trending things, for computing
smoothing average
"""
import math

from shinken.load import Load


class Trender:
    def __init__(self, chunk_interval):
        self.chunk_interval = chunk_interval
        self.nb_chunks = int(math.ceil(86400.0/self.chunk_interval))


        # Ok a quick and dirty load computation
    def quick_update(self, prev_val, new_val, m, interval):
        l = Load(m=m, initial_value=prev_val)
        l.update_load(new_val, interval)
        return l.get_load()


    def get_previous_chunk(self, wday, chunk_nb):
        if chunk_nb == 0:
            chunk_nb = self.nb_chunks - 1
            wday -= 1
        else:
            chunk_nb -= 1
        wday = wday % 7
        return (wday, chunk_nb)



    
