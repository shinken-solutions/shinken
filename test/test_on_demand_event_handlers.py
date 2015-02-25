#!/usr/bin/env python2
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
# This file is used to test acknowledge of problems
#

from shinken_test import *


class TestConfig(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_on_demand_event_handlers.cfg')

    def test_on_demand_eh(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.assertEqual(False, svc.event_handler_enabled)

        self.scheduler_loop(5, [[svc, 2, 'CRITICAL']])
        # We should NOT see any event hnalder here :)
        self.assert_no_log_match('SERVICE EVENT HANDLER')
        print "MY Actions", self.sched.actions

        # And now we ask for a launch in manual
        now = time.time()
        cmd = "[%lu] LAUNCH_SVC_EVENT_HANDLER;test_host_0;test_ok_0" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assert_any_log_match('SERVICE EVENT HANDLER')




if __name__ == '__main__':
    unittest.main()
