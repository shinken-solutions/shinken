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

import time


class LiveStatusCounters:  # (LiveStatus):
    def __init__(self):
        self.counters = {
            'neb_callbacks': 0,
            'connections': 0,
            'service_checks': 0,
            'host_checks': 0,
            'forks': 0,
            'log_message': 0,
            'external_commands': 0
        }
        self.last_counters = {
            'neb_callbacks': 0,
            'connections': 0,
            'service_checks': 0,
            'host_checks': 0,
            'forks': 0,
            'log_message': 0,
            'external_commands': 0
        }
        self.rate = {
            'neb_callbacks': 0.0,
            'connections': 0.0,
            'service_checks': 0.0,
            'host_checks': 0.0,
            'forks': 0.0,
            'log_message': 0.0,
            'external_commands': 0.0
        }
        self.last_update = 0
        self.interval = 10
        self.rating_weight = 0.25

    def increment(self, counter):
        if counter in self.counters:
            self.counters[counter] += 1

    def calc_rate(self):
        elapsed = time.time() - self.last_update
        if elapsed > self.interval:
            self.last_update = time.time()
            for counter in self.counters:
                delta = self.counters[counter] - self.last_counters[counter]
                new_rate = delta / elapsed
                if self.rate[counter] == 0:
                    avg_rate = new_rate
                else:
                    avg_rate = self.rate[counter] * (1 - self.rating_weight) + new_rate * self.rating_weight
                self.rate[counter] = avg_rate
                self.last_counters[counter] = self.counters[counter]

    def count(self, counter):
        if counter in self.counters:
            return self.counters[counter]
        elif counter.endswith('_rate'):
            if counter[0:-5] in self.rate:
                return self.rate[counter[0:-5]]
            else:
                return 0.0
        else:
            return 0
