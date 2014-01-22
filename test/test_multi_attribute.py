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
        self.assert_(hst1 is not None)
        self.assert_(srv1 is not None)

        # inherited parameter
        self.assert_(hst1.active_checks_enabled is True)
        self.assert_(srv1.active_checks_enabled is True)

        # non list parameter (only the last value set should remain)
        self.assert_(hst1.max_check_attempts == 3)
        self.assert_(srv1.max_check_attempts == 3)

        # list parameter (all items should appear in the order they are defined)
        self.assert_(hst1.notification_options == ['+1', 's', 'f', 'r', 'u', 'd'])
        self.assert_(srv1.notification_options == ['+1', 's', 'f', 'r', 'c', 'u', 'w'])


class TestConfigBroken(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_multi_attribute_broken.cfg')

    def test_multi_valued_attribute_errors(self):
        self.assert_(not self.conf.conf_is_correct)

        # Get the arbiter's log broks
        [b.prepare() for b in self.broks.values()]
        logs = [b.data['log'] for b in self.broks.values() if b.type == 'log']

        self.assert_(len([log for log in logs if re.search(r'no support for _ syntax in multiple valued attributes', log)]) == 1)


if __name__ == '__main__':
    unittest.main()
