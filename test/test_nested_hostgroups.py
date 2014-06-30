#!/usr/bin/env python
# Copyright (C) 2009-2010:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
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

#
# This file is used to test reading and processing of config files
#

from shinken_test import *


class TestNestedHostgroups(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_nested_hostgroups.cfg')

    # We got the service "NestedService" apply in High level
    # group. And this one got a sub group, low one. each got ONE
    # Host, so we must have this servie on both.
    def test_lookup_nested_hostgroups(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        router = self.sched.hosts.find_by_name("test_router_0")
        hg_high = self.sched.conf.hostgroups.find_by_name('high_level')
        self.assert_(hg_high is not None)
        self.assert_(host in hg_high.members)
        self.assert_(router in hg_high.members)
        hg_low = self.sched.conf.hostgroups.find_by_name('low_level')
        self.assert_(hg_low is not None)
        self.assert_(host in hg_low.members)
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "NestedService")
        self.assert_(svc1 is not None)
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "NestedService")
        self.assert_(svc2 is not None)

        # And now look for the service testHostToGroup apply on the group
        # high_level, and the host test_host_2 should be on it, so it must have
        # this service too
        host2 = self.sched.hosts.find_by_name("test_host_2")
        self.assert_(host2 in hg_high.members)
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_host_2", "testHostToGroup")
        self.assert_(svc3 is not None)

        # And same with an host in the low_group, should have it too
        host3 = self.sched.hosts.find_by_name("test_host_3")
        self.assert_(host3 in hg_high.members)
        svc4 = self.sched.services.find_srv_by_name_and_hostname("test_host_3", "testHostToGroup")
        self.assert_(svc4 is not None)



if __name__ == '__main__':
    unittest.main()
