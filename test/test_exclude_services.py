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
from functools import partial

import re
from shinken_test import unittest, ShinkenTest


class TestPropertyOverride(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/exclude_include_services.cfg')

    def test_exclude_services(self):
        hst1 = self.sched.hosts.find_by_name("test_host_01")
        hst2 = self.sched.hosts.find_by_name("test_host_02")

        self.assertEqual([], hst1.service_excludes)
        self.assertEqual(["srv-svc11", "srv-svc21", "proc proc1"], hst2.service_excludes)

        Find = self.sched.services.find_srv_by_name_and_hostname

        # All services should exist for test_host_01
        find = partial(Find, 'test_host_01')
        for svc in (
            'srv-svc11', 'srv-svc12',
            'srv-svc21', 'srv-svc22',
            'proc proc1', 'proc proc2',
        ):
            self.assertIsNotNone(find(svc))

        # Half the services only should exist for test_host_02
        find = partial(Find, 'test_host_02')
        for svc in ('srv-svc12', 'srv-svc22', 'proc proc2'):
            self.assertIsNotNone(find(svc))

        for svc in ('srv-svc11', 'srv-svc21', 'proc proc1'):
            self.assertIsNone(find(svc))

        # 2 and 21 should not exist on test-04
        find = partial(Find, 'test_host_04')
        for svc in ('srv-svc11', 'srv-svc12', 'proc proc1'):
            self.assertIsNotNone(find(svc))

        for svc in ('srv-svc21', 'srv-svc22', 'proc proc2'):
            self.assertIsNone(find(svc))

        # no service should be defined on test_host_05
        find = partial(Find, 'test_host_05')
        for svc in ('srv-svc11', 'srv-svc12', 'proc proc1',
                    'srv-svc21', 'srv-svc22', 'proc proc2'):
            self.assertIsNone(find(svc))


    def test_service_includes(self):
        Find = self.sched.services.find_srv_by_name_and_hostname
        find = partial(Find, 'test_host_03')

        for svc in ('srv-svc11', 'proc proc2', 'srv-svc22'):
            self.assertIsNotNone(find(svc))

        for svc in ('srv-svc12', 'srv-svc21', 'proc proc1'):
            self.assertIsNone(find(svc))


if __name__ == '__main__':
    unittest.main()
