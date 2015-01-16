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
# This file is used to test multi valued attribute feature.
#

import re
from shinken_test import unittest, ShinkenTest


class TestMultiVuledAttributes(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_multi_attribute.cfg')

    def test_multi_valued_attributes(self):
        hst1 = self.sched.hosts.find_by_name("test_host_01")
        srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        self.assertIsNot(hst1, None)
        self.assertIsNot(srv1, None)

        # inherited parameter
        self.assertIs(True, hst1.active_checks_enabled)
        self.assertIs(True, srv1.active_checks_enabled)

        # non list parameter (only the last value set should remain)
        self.assertEqual(3, hst1.max_check_attempts)
        self.assertEqual(3, srv1.max_check_attempts)

        # list parameter (all items should appear in the order they are defined)
        self.assertEqual([u'd', u'f', u'1', u's', u'r', u'u'], list(set(hst1.notification_options)))

        self.assertEqual([u'c', u'f', u'1', u's', u'r', u'u', u'w'], list(set(srv1.notification_options)))



if __name__ == '__main__':
    unittest.main()
