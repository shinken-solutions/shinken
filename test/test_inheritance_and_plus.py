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


class TestInheritanceAndPlus(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_inheritance_and_plus.cfg')

    def test_inheritance_and_plus(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        linux = self.sched.hostgroups.find_by_name('linux')
        self.assert_(linux is not None)
        dmz = self.sched.hostgroups.find_by_name('DMZ')
        self.assert_(dmz is not None)
        mysql = self.sched.hostgroups.find_by_name('mysql')
        self.assert_(mysql is not None)

        host1 = self.sched.hosts.find_by_name("test-server1")
        host2 = self.sched.hosts.find_by_name("test-server2")
        # HOST 1 is lin-servers,dmz, so should be in linux AND DMZ group
        for hg in host1.hostgroups:
            print hg.get_name()
        self.assert_(linux in host1.hostgroups)
        self.assert_(dmz in host1.hostgroups)

        # HOST2 is in lin-servers,dmz and +mysql, so all three of them
        for hg in host2.hostgroups:
            print hg.get_name()
        self.assert_(linux in host2.hostgroups)
        self.assert_(dmz in host2.hostgroups)
        self.assert_(mysql in host2.hostgroups)




if __name__ == '__main__':
    unittest.main()
