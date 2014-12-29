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


class TestWarnAboutNoBrokerInRealm(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_no_broker_in_realm_warning.cfg')

    def test_no_broker_in_realm_warning(self):
        dist = self.conf.realms.find_by_name("Distant")
        self.assertIsNot(dist, None)
        sched = self.conf.schedulers.find_by_name("Scheduler-distant")
        self.assertIsNot(sched, None)
        self.assertEqual(0, len(sched.realm.potential_brokers))


if __name__ == '__main__':
    unittest.main()
