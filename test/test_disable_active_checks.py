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
# This file is used to test reading and processing of config files
#

from shinken_test import *


class TestDisableActiveChecks(ShinkenTest):

    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/nagios_disable_active_checks.cfg')


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
        self.assert_(host.state == 'UP')
        self.assert_(host.state_type == 'HARD')
        last_output = host.output

        host.schedule()
        self.sched.external_command.DISABLE_HOST_CHECK(host)

        c = host.checks_in_progress.pop()
        print c.__dict__
        print c.status
        self.assert_(c.status == 'waitconsume')
        self.scheduler_loop(2, [])

        print host.state
        print host.output
        self.assert_(host.output == last_output)

        print len(host.checks_in_progress)
        print host.in_checking
        self.assert_(host.in_checking == False)




if __name__ == '__main__':
    unittest.main()
