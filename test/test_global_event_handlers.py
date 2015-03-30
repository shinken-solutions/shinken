#!/usr/bin/env python
# Copyright (C) 2009-2014:
#    Sebastien Coavoux <s.coavoux@free.fr>
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
        self.setup_with_file('etc/shinken_global_event_handlers.cfg')

    def test_global_eh(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_02")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        self.assertEqual(True, svc.event_handler_enabled)
        self.assertEqual(True, svc.__class__.enable_event_handlers)
        self.assertEqual("eventhandler", svc.global_event_handler.command.command_name)

        self.scheduler_loop(5, [[svc, 2, 'CRITICAL']])
        self.assert_any_log_match('EVENT HANDLER')
        print "MY Actions", self.sched.actions






if __name__ == '__main__':
    unittest.main()
