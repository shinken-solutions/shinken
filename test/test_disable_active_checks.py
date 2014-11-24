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


class TestDisableActiveChecks(ShinkenTest):

    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/shinken_disable_active_checks.cfg')


    # We try to disable the actie checks and see if it's really done
    # with a dummy check, so we need to get the same state and output
    def test_disable_active_checks(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")

        print "Checks in progress", host.checks_in_progress
        c = host.checks_in_progress.pop()
        print c.__dict__
        print c.status

        self.scheduler_loop(1, [[host, 0, 'I set this host UP | value1=1 value2=2']])
        self.assertEqual('UP', host.state)
        self.assertEqual('HARD', host.state_type)
        last_output = host.output

        host.schedule()
        self.sched.external_command.DISABLE_HOST_CHECK(host)

        c = host.checks_in_progress.pop()
        print c.__dict__
        print c.status
        self.assertEqual('waitconsume', c.status)
        self.scheduler_loop(2, [])

        print host.state
        print host.output
        self.assertEqual(last_output, host.output)

        print len(host.checks_in_progress)
        print host.in_checking
        self.assertEqual(False, host.in_checking)




if __name__ == '__main__':
    unittest.main()
