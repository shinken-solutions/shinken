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
# This file is used to test object properties overriding.
#

from shinken_test import unittest, ShinkenTest
import re


class TestInitialState(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_initial_state.cfg')

    def test_initial_state(self):
        host0 = self.sched.hosts.find_by_name("test_host_0")
        host1 = self.sched.hosts.find_by_name("test_host_1")
        svc00 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_service_0")
        svc01 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_service_1")
        svc10 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_service_0")
        svc11 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_service_1")

        self.assertIsNotNone(host0)
        self.assertIsNotNone(host1)
        self.assertIsNotNone(svc00)
        self.assertIsNotNone(svc01)
        self.assertIsNotNone(svc10)
        self.assertIsNotNone(svc11)

        self.assertEqual(host0.state, "PENDING")
        self.assertEqual(host0.state_id, 0)
        self.assertEqual(host0.output, "")
        self.assertEqual(host1.state, "DOWN")
        self.assertEqual(host1.state_id, 1)
        self.assertEqual(host1.output, "No host result received")
        self.assertEqual(svc00.state, "PENDING")
        self.assertEqual(svc00.state_id, 0)
        self.assertEqual(svc00.output, "")
        self.assertEqual(svc01.state, "CRITICAL")
        self.assertEqual(svc01.state_id, 2)
        self.assertEqual(svc01.output, "No sevrvice result received")
        self.assertEqual(svc10.state, "PENDING")
        self.assertEqual(svc10.state_id, 0)
        self.assertEqual(svc10.output, "")
        self.assertEqual(svc11.state, "CRITICAL")
        self.assertEqual(svc11.state_id, 2)
        self.assertEqual(svc11.output, "No sevrvice result received")

        self.scheduler_loop(1, [
            [host0, 0, 'UP test_host_0'],
            [host1, 0, 'UP test_host_1'],
            [svc00, 0, 'OK test_host_0/test_service_0'],
            [svc01, 0, 'OK test_host_0/test_service_1'],
            [svc10, 0, 'OK test_host_1/test_service_0'],
            [svc11, 0, 'OK test_host_1/test_service_1'],
        ], do_sleep=True)

        self.assertEqual(host0.state, "UP")
        self.assertEqual(host0.state_id, 0)
        self.assertEqual(host0.output, "UP test_host_0")
        self.assertEqual(host1.state, "UP")
        self.assertEqual(host1.state_id, 0)
        self.assertEqual(host1.output, "UP test_host_1")
        self.assertEqual(svc00.state, "OK")
        self.assertEqual(svc00.state_id, 0)
        self.assertEqual(svc00.output, "OK test_host_0/test_service_0")
        self.assertEqual(svc01.state, "OK")
        self.assertEqual(svc01.state_id, 0)
        self.assertEqual(svc01.output, "OK test_host_0/test_service_1")
        self.assertEqual(svc10.state, "OK")
        self.assertEqual(svc10.state_id, 0)
        self.assertEqual(svc10.output, "OK test_host_1/test_service_0")
        self.assertEqual(svc11.state, "OK")
        self.assertEqual(svc11.state_id, 0)
        self.assertEqual(svc11.output, "OK test_host_1/test_service_1")


class TestInitialStateBadConf(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_initial_state_bad.cfg')

    def test_bad_conf(self):
        self.assertFalse(self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']

        self.assertEqual(1, len([log for log in logs if re.search('invalid initial_state: a, should be one of u, d', log)]) )
        self.assertEqual(1, len([log for log in logs if re.search('invalid initial_state: a, should be one of c, u, w, o', log)]) )

if __name__ == '__main__':
    unittest.main()
