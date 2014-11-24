#!/usr/bin/env python
# Copyright (C) 2009-2014:
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


class TestStarMemberGroup(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_startmember_group.cfg')

    # Check if service apply on a hostgroup * is good or not
    def test_starmembergroupdef(self):
        hg = self.sched.conf.hostgroups.find_by_name('ping-servers')
        self.assertIsNot(hg, None)
        print hg.members
        h = self.sched.conf.hosts.find_by_name('test_host_0')
        r = self.sched.conf.hosts.find_by_name('test_router_0')
        self.assertIn(h, hg.members)
        self.assertIn(r, hg.members)

        s = self.sched.conf.services.find_srv_by_name_and_hostname('test_host_0', 'PING')
        self.assertIsNot(s, None)


if __name__ == '__main__':
    unittest.main()
