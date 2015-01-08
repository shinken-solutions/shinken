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


class TestRealms(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_realms.cfg')

    # We check for each host, if they are in the good realm
    def test_realm_assigntion(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        realm1 = self.conf.realms.find_by_name('realm1')
        self.assertIsNot(realm1, None)
        realm2 = self.conf.realms.find_by_name('realm2')
        self.assertIsNot(realm2, None)
        test_host_realm1 = self.sched.hosts.find_by_name("test_host_realm1")
        self.assertIsNot(test_host_realm1, None)
        self.assertEqual(realm1.get_name(), test_host_realm1.realm)
        test_host_realm2 = self.sched.hosts.find_by_name("test_host_realm2")
        self.assertIsNot(test_host_realm2, None)
        self.assertEqual(realm2.get_name(), test_host_realm2.realm)

    # We check for each host, if they are in the good realm
    # but when they are apply in a hostgroup link
    def test_realm_hostgroup_assigntion(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        in_realm2 = self.sched.hostgroups.find_by_name('in_realm2')
        realm1 = self.conf.realms.find_by_name('realm1')
        self.assertIsNot(realm1, None)
        realm2 = self.conf.realms.find_by_name('realm2')
        self.assertIsNot(realm2, None)
        # 1 and 2 are link to realm2 because they are in the hostgroup in_realm2
        test_host1_hg_realm2 = self.sched.hosts.find_by_name("test_host1_hg_realm2")
        self.assertIsNot(test_host1_hg_realm2, None)
        self.assertEqual(realm2.get_name(), test_host1_hg_realm2.realm)
        self.assertIn(in_realm2.get_name(), [hg.get_name() for hg in test_host1_hg_realm2.hostgroups])

        test_host2_hg_realm2 = self.sched.hosts.find_by_name("test_host2_hg_realm2")
        self.assertIsNot(test_host2_hg_realm2, None)
        self.assertEqual(realm2.get_name(), test_host2_hg_realm2.realm)
        self.assertIn(in_realm2.get_name(), [hg.get_name() for hg in test_host2_hg_realm2.hostgroups])

        test_host3_hg_realm2 = self.sched.hosts.find_by_name("test_host3_hg_realm2")
        self.assertIsNot(test_host3_hg_realm2, None)
        self.assertEqual(realm1.get_name(), test_host3_hg_realm2.realm)
        self.assertIn(in_realm2.get_name(), [hg.get_name() for hg in test_host3_hg_realm2.hostgroups])


    # Realms should be stripped when linking to hosts and hostgroups
    # so we don't pickle the whole object, but just a name
    def test_realm_stripping_before_sending(self):
        test_host_realm1 = self.sched.hosts.find_by_name("test_host_realm1")
        self.assertIsNot(test_host_realm1, None)
        print type(test_host_realm1.realm)
        self.assertTrue(isinstance(test_host_realm1.realm, basestring))

        in_realm2 = self.sched.hostgroups.find_by_name('in_realm2')
        self.assertIsNot(in_realm2, None)
        print type(in_realm2.realm)
        self.assertTrue(isinstance(in_realm2.realm, basestring))


    def test_sub_realms_assignations(self):
        world = self.conf.realms.find_by_name('World')
        self.assertIsNot(world, None)
        europe = self.conf.realms.find_by_name('Europe')
        self.assertIsNot(europe, None)
        paris = self.conf.realms.find_by_name('Paris')
        self.assertIsNot(paris, None)
        # Get the broker in the realm level
        bworld = self.conf.brokers.find_by_name('B-world')
        self.assertIsNot(bworld, None)

        world.prepare_for_satellites_conf()
        europe.prepare_for_satellites_conf()
        paris.prepare_for_satellites_conf()

        print world.__dict__
        # broker should be in the world level
        self.assertIs(bworld in world.potential_brokers, True)
        # in europe too
        self.assertIs(bworld in europe.potential_brokers, True)
        # and in paris too
        self.assertIs(bworld in paris.potential_brokers, True)
        


if __name__ == '__main__':
    unittest.main()
