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
# This file is used to test hostgroups and regex expressions expansion in
# business rules.
#

from shinken_test import unittest, ShinkenTest, time
from shinken.misc import datamanager
from shinken.misc.filter import only_related_to

# Set this variable False to disable profiling test
PROFILE_BP_RULE_RE_PROCESSING = False


class TestDatamanager(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_misc_filter.cfg')

    def test_get_all_problems(self):
        srv1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        srv2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")
        srv3 = self.sched.services.find_srv_by_name_and_hostname("test_host_03", "srv3")

        ctc1 = self.sched.contacts.find_by_name("contact_01")
        ctc2 = self.sched.contacts.find_by_name("contact_02")
        ctc3 = self.sched.contacts.find_by_name("contact_03")

        dm = datamanager.DataManager()
        dm.load(self.sched)

        self.scheduler_loop(1, [
            [srv1, 2, 'CRIT srv1'],
            [srv2, 2, 'CRIT srv2'],
            [srv3, 2, 'CRIT srv3']])

        items = dm.get_all_problems()
        self.assert_(len(items) == 3)
        self.assert_(len(only_related_to(items, ctc1)) == 3)
        self.assert_(len(only_related_to(items, ctc2)) == 3)
        self.assert_(len(only_related_to(items, ctc3)) == 0)
        ctc2.hide_ui_problems = True
        self.assert_(len(only_related_to(items, ctc2)) == 1)
        ctc1.hide_ui_problems = True
        self.assert_(len(only_related_to(items, ctc1)) == 1)


if __name__ == '__main__':
    unittest.main()
