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


class TestConfig(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_host_without_cmd.cfg')

    def test_host_is_pending(self):
        self.print_header()
        # first of all, a host without check_command must be valid
        self.assertTrue(self.conf.conf_is_correct)
        # service always ok, host stays pending
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        for c in host.checks_in_progress:
            # hurry up, we need an immediate result
            c.t_to_go = 0
        # scheduler.schedule() always schedules a check, even for this
        # kind of hosts
        #host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        host.checks_in_progress = []
        host.in_checking = False
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        # this time we need the dependency from service to host
        #svc.act_depend_of = [] # no hostchecks on critical checkresults

        # initially the host is pending
        self.assertEqual('PENDING', host.state)
        self.assertEqual('PENDING', svc.state)
        # now force a dependency check of the host
        self.scheduler_loop(2, [[svc, 2, 'BAD | value1=0 value2=0']])
        self.show_actions()
        # and now the host is magically UP
        self.assertEqual('UP', host.state)
        self.assertEqual('HARD', host.state_type)
        self.assertEqual('Host assumed to be UP', host.output)



if __name__ == '__main__':
    unittest.main()
