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


class TestHostspecialSched(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_nohostsched.cfg')

    # The hosts can have no check_period nor check_interval.
    # It's valid, and say: 24x7 and 5min interval in fact.
    def test_nohostsched(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("moncul")
        self.assertIsNot(host, None)
        print "check", host.next_chk
        print "Check in", host.next_chk - now
        self.assertLess(host.next_chk - now, 301)
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        print "Loop"
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2']])
        self.assertEqual('UP', host.state)
        self.assertEqual('HARD', host.state_type)
        # Reschedule the host as a normal way
        host.schedule()
        print "Final", host.next_chk, host.in_checking
        print "Next check?", host.next_chk - now
        print "Next check should be still < 300", host.next_chk - now
        self.assertLess(host.next_chk - now, 301)
        # but in 5min in fact, so more than 290,
        # something like 299.0
        self.assertGreater(host.next_chk - now, 290)



if __name__ == '__main__':
    unittest.main()
