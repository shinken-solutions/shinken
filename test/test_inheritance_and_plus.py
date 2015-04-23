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
        self.assertIsNot(linux, None)
        dmz = self.sched.hostgroups.find_by_name('DMZ')
        self.assertIsNot(dmz, None)
        mysql = self.sched.hostgroups.find_by_name('mysql')
        self.assertIsNot(mysql, None)

        host1 = self.sched.hosts.find_by_name("test-server1")
        host2 = self.sched.hosts.find_by_name("test-server2")
        # HOST 1 is lin-servers,dmz, so should be in linux AND DMZ group
        for hg in host1.hostgroups:
            print hg.get_name()
        self.assertIn(linux.get_name(), [hg.get_name() for hg in host1.hostgroups])
        self.assertIn(dmz.get_name(), [hg.get_name() for hg in host1.hostgroups])

        # HOST2 is in lin-servers,dmz and +mysql, so all three of them
        for hg in host2.hostgroups:
            print hg.get_name()
        self.assertIn(linux.get_name(), [hg.get_name() for hg in host2.hostgroups])
        self.assertIn(dmz.get_name(), [hg.get_name() for hg in host2.hostgroups])
        self.assertIn(mysql.get_name(), [hg.get_name() for hg in host2.hostgroups])

        service = self.sched.services.find_srv_by_name_and_hostname("pack-host", 'CHILDSERV')
        sgs = [sg.get_name() for sg in service.servicegroups]
        self.assertIn("generic-sg", sgs)
        self.assertIn("another-sg", sgs)

    def test_pack_like_inheritance(self):
        # get our pack service
        host = self.sched.hosts.find_by_name('pack-host')
        service = host.find_service_by_name('CHECK-123')

        # it should exist
        self.assertIsNotNone(service)

        # it should contain the custom variable `_CUSTOM_123` because custom
        # variables are always stored in upper case
        customs = service.customs
        self.assertIn('_CUSTOM_123', customs)


if __name__ == '__main__':
    unittest.main()
