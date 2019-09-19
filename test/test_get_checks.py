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

from __future__ import absolute_import
from shinken_test import *
import time


class TestPollerTagGetchecks(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_get_checks.cfg')

    def test_get_whole_checks(self):
        self.sched.schedule()
        self.sched.get_new_actions()
        checks = self.sched.checks
        time.sleep(60)

        self.assertEqual(len(checks), 12)

        for c in checks.values():
            self.assertEqual(c.status, "scheduled")
            self.assertEquals(c.worker, "none")

        in_poller = self.sched.get_to_run_checks(
            do_checks=True,
            do_actions=False,
            worker_name='test')

        self.assertTrue(len(in_poller), 12)

        for c in checks.values():
            self.assertEqual(c.status, "inpoller")
            self.assertEquals(c.worker, "test")

    def test_get_most_urgent_checks(self):
        self.sched.schedule()
        self.sched.get_new_actions()
        checks = self.sched.checks
        time.sleep(60)

        self.assertEqual(len(checks), 12)

        for c in checks.values():
            self.assertEqual(c.status, "scheduled")
            self.assertEquals(c.worker, "none")

        in_poller = self.sched.get_to_run_checks(
            do_checks=True,
            do_actions=False,
            worker_name='test',
            max_actions=3)

        self.assertTrue(len(in_poller), 3)

        for c in checks.values():
            if c.priority == 10:
                self.assertEqual(c.status, "inpoller")
                self.assertEquals(c.worker, "test")
            else:
                self.assertEqual(c.status, "scheduled")
                self.assertEquals(c.worker, "none")


if __name__ == '__main__':
    unittest.main()
