#!/usr/bin/python

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

"""
Helper functions for some sorting
"""


# Sort hosts and services by impact, states and co
def hst_srv_sort(s1, s2):
    if s1.business_impact > s2.business_impact:
        return -1
    if s2.business_impact > s1.business_impact:
        return 1

    # Ok, we compute a importance value so
    # For host, the order is UP, UNREACH, DOWN
    # For service: OK, UNKNOWN, WARNING, CRIT
    # And DOWN is before CRITICAL (potential more impact)
    tab = {'host': {0: 0, 1: 4, 2: 1},
           'service': {0: 0, 1: 2, 2: 3, 3: 1}
           }
    state1 = tab[s1.__class__.my_type].get(s1.state_id, 0)
    state2 = tab[s2.__class__.my_type].get(s2.state_id, 0)
    # ok, here, same business_impact
    # Compare warn and crit state
    if state1 > state2:
        return -1
    if state2 > state1:
        return 1

    # Ok, so by name...
    if s1.get_full_name() > s2.get_full_name():
        return 1
    else:
        return -1


# Sort hosts and services by impact, states and co
def worse_first(s1, s2):
    # Ok, we compute a importance value so
    # For host, the order is UP, UNREACH, DOWN
    # For service: OK, UNKNOWN, WARNING, CRIT
    # And DOWN is before CRITICAL (potential more impact)
    tab = {'host': {0: 0, 1: 4, 2: 1},
           'service': {0: 0, 1: 2, 2: 3, 3: 1}
           }
    state1 = tab[s1.__class__.my_type].get(s1.state_id, 0)
    state2 = tab[s2.__class__.my_type].get(s2.state_id, 0)

    # ok, here, same business_impact
    # Compare warn and crit state
    if state1 > state2:
        return -1
    if state2 > state1:
        return 1

    # Same? ok by business impact
    if s1.business_impact > s2.business_impact:
        return -1
    if s2.business_impact > s1.business_impact:
        return 1

    # Ok, so by name...
    # Ok, so by name...
    if s1.get_full_name() > s2.get_full_name():
        return -1
    else:
        return 1


# Sort hosts and services by last_state_change time
def last_state_change_earlier(s1, s2):
    # ok, here, same business_impact
    # Compare warn and crit state
    if s1.last_state_change > s2.last_state_change:
        return -1
    if s1.last_state_change < s2.last_state_change:
        return 1

    return 0
