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
# This file is used to test acknowledge of problems
#

from shinken_test import *

# Restore sleep functions
time_hacker.set_real_time()



class TestAcksWithExpire(ShinkenTest):

    def test_ack_hard_service_with_expire(self):
        self.print_header()
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
        self.scheduler_loop(1, [[host, 0, 'UP']])
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual(0, svc.current_notification_number)

        #--------------------------------------------------------------
        # first check the normal behavior
        # service reaches hard;2
        # at the end there must be 3 actions: eventhandler hard,
        #   master notification and contact notification
        #--------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        self.assertEqual(1, svc.current_notification_number)
        self.assertEqual(3, self.count_actions())
        self.assert_log_match(5, 'SERVICE NOTIFICATION')
        self.show_and_clear_logs()
        self.show_actions()

        #--------------------------------------------------------------
        # stay hard and wait for the second notification (notification_interval)
        #--------------------------------------------------------------
        print "- 2 x BAD stay hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=False)
        self.show_and_clear_logs()
        self.show_actions()

        #--------------------------------------------------------------
        # admin wakes up and acknowledges the problem
        # the ACK is the only log message
        # a master notification is still around, but can't be sent
        #--------------------------------------------------------------
        self.assertFalse(svc.problem_has_been_acknowledged)
        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM_EXPIRE;test_host_0;test_ok_0;1;1;0;%d;lausser;blablub" % (now, int(now) + 5)
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [], do_sleep=False)
        self.assertTrue(svc.problem_has_been_acknowledged)
        self.assert_log_match(1, 'ACKNOWLEDGEMENT \(CRITICAL\)')
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=False)
        self.assertEqual(1, self.count_logs())
        self.assertEqual(1, self.count_actions())
        self.show_and_clear_logs()
        self.show_actions()

        #--------------------------------------------------------------
        # Wait 4 remove acknowledgement
        # now notifications are sent again
        #--------------------------------------------------------------
        time.sleep(5)
        # Wait a bit
        self.sched.check_for_expire_acknowledge()
        self.assertFalse(svc.problem_has_been_acknowledged)

        #now = time.time()
        #cmd = "[%lu] REMOVE_SVC_ACKNOWLEDGEMENT;test_host_0;test_ok_0" % now
        #self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.show_logs()
        self.show_actions()
        # the contact notification was sent immediately (t_to_go)
        self.assertFalse(svc.problem_has_been_acknowledged)
        self.show_logs()
        self.show_actions()


if __name__ == '__main__':
    unittest.main()
