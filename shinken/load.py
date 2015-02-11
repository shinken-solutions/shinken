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
import math


class Load:
    """This class is for having a easy Load calculation
    without having to send value at regular interval
    (but it's more efficient if you do this :) ) and without
    having a list or other stuff. It's just an object, an update and a get
    You can define m: the average for m minutes. The val is
    the initial value. It's better if it's 0 but you can choose.

    """

    def __init__(self, m=1, initial_value=0):
        self.exp = 0  # first exp
        self.m = m  # Number of minute of the avg
        self.last_update = 0  # last update of the value
        self.val = initial_value  # first value


    def update_load(self, new_val, forced_interval=None):
        # The first call do not change the value, just tag
        # the beginning of last_update
        # IF  we force : bail out all time thing
        if not forced_interval and self.last_update == 0:
            self.last_update = time.time()
            return
        now = time.time()
        try:
            if forced_interval:
                diff = forced_interval
            else:
                diff = now - self.last_update
            self.exp = 1 / math.exp(diff / (self.m * 60.0))
            self.val = new_val + self.exp * (self.val - new_val)
            self.last_update = now
        except OverflowError:  # if the time change without notice, we overflow :(
            pass
        except ZeroDivisionError:  # do not care
            pass

    def get_load(self):
        return self.val


if __name__ == '__main__':
    l = Load()
    t = time.time()
    for i in xrange(1, 300):
        l.update_load(1)
        print '[', int(time.time() - t), ']', l.get_load(), l.exp
        time.sleep(5)
