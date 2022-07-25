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

from __future__ import absolute_import, division, print_function, unicode_literals

from shinken_test import *


class TestPollerTagGetchecks(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_priority.cfg')

    def test_host_check_priority(self):
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_host_1 = self.sched.hosts.find_by_name("test_host_1")
        test_host_2 = self.sched.hosts.find_by_name("test_host_2")

        self.assertEqual(test_host_0.priority, 100)
        self.assertEqual(test_host_1.priority, 100)
        self.assertEqual(test_host_2.priority, 50)
        self.assertEqual(test_host_0.check_command.priority, 100)
        self.assertEqual(test_host_1.check_command.priority, 10)
        self.assertEqual(test_host_2.check_command.priority, 50)

    def test_service_check_priority(self):
        test_svc_00 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_0", "standard_service")
        test_svc_01 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_0", "hi_prio_service")
        test_svc_02 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_0", "med_prio_service")

        self.assertEqual(test_svc_00.priority, 100)
        self.assertEqual(test_svc_01.priority, 100)
        self.assertEqual(test_svc_02.priority, 40)
        self.assertEqual(test_svc_00.check_command.priority, 100)
        self.assertEqual(test_svc_01.check_command.priority, 10)
        self.assertEqual(test_svc_02.check_command.priority, 40)

        test_svc_10 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_1", "standard_service")
        test_svc_11 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_1", "hi_prio_service")
        test_svc_12 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_1", "med_prio_service")

        self.assertEqual(test_svc_10.priority, 100)
        self.assertEqual(test_svc_11.priority, 100)
        self.assertEqual(test_svc_12.priority, 40)
        self.assertEqual(test_svc_10.check_command.priority, 100)
        self.assertEqual(test_svc_11.check_command.priority, 10)
        self.assertEqual(test_svc_12.check_command.priority, 40)

        test_svc_20 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_2", "standard_service")
        test_svc_21 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_2", "hi_prio_service")
        test_svc_22 = self.sched.services.find_srv_by_name_and_hostname(
            "test_host_2", "med_prio_service")

        self.assertEqual(test_svc_20.priority, 50)
        self.assertEqual(test_svc_21.priority, 50)
        self.assertEqual(test_svc_22.priority, 40)
        self.assertEqual(test_svc_20.check_command.priority, 50)
        self.assertEqual(test_svc_21.check_command.priority, 50)
        self.assertEqual(test_svc_22.check_command.priority, 40)


if __name__ == '__main__':
    unittest.main()
