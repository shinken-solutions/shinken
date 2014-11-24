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


class TestUnknownNotChangeState(ShinkenTest):

    # Uncomment this is you want to use a specific configuration
    # for your test
    #def setUp(self):
    #    self.setup_with_file('etc/shinken_1r_1h_1s.cfg')


    # We got problem with unknown results on bad connections
    # for critical services and host: if it was in a notification pass
    # then the notification is restarted, but it's just a missing data,
    # not a reason to warn about it
    def test_unknown_do_not_change_state(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        print "GO OK" * 10
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'OK | value1=0 value2=0']])
        self.assertEqual('OK', svc.state)
        self.assertEqual('HARD', svc.state_type)

        print "GO CRITICAL SOFT" * 10
        # Ok we are UP, now we seach to go in trouble
        self.scheduler_loop(1, [[svc, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/SOFT
        self.assertEqual('CRITICAL', svc.state)
        self.assertEqual('SOFT', svc.state_type)
        # And again and again :)
        print "GO CRITICAL HARD" * 10
        self.scheduler_loop(2, [[svc, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/HARD
        self.assertEqual('CRITICAL', svc.state)
        self.assertEqual('HARD', svc.state_type)

        # Should have a notification about it
        self.assert_any_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

        print "GO UNKNOWN HARD" * 10
        # Then we make it as a unknown state
        self.scheduler_loop(1, [[svc, 3, 'Unknown | value1=1 value2=2']])
        # And we DO NOT WANT A NOTIF HERE
        self.assert_no_log_match('SERVICE NOTIFICATION.*;UNKNOWN')
        self.show_and_clear_logs()

        print "Return CRITICAL HARD" * 10
        # Then we came back as CRITICAL
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | value1=1 value2=2']])
        print svc.state, svc.state_type
        self.assert_no_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

        print "Still CRITICAL HARD" * 10
        # Then we came back as CRITICAL
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | value1=1 value2=2']])
        print svc.state, svc.state_type
        self.assert_no_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

        # We check if we can still have new notifications of course
        # And we speedup the notification
        for n in svc.notifications_in_progress.values():
            n.t_to_go = time.time()
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | value1=1 value2=2']])
        print svc.state, svc.state_type
        self.assert_any_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

    # We got problem with unknown results on bad connections
    # for critical services and host: if it was in a notification pass
    # then the notification is restarted, but it's just a missing data,
    # not a reason to warn about it
    def test_unknown_do_not_change_state_with_different_exit_status_phase(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        print "GO OK" * 10
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'OK | value1=0 value2=0']])
        self.assertEqual('OK', svc.state)
        self.assertEqual('HARD', svc.state_type)

        print "GO CRITICAL SOFT" * 10
        # Ok we are UP, now we seach to go in trouble
        self.scheduler_loop(1, [[svc, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/SOFT
        self.assertEqual('CRITICAL', svc.state)
        self.assertEqual('SOFT', svc.state_type)
        # And again and again :)
        print "GO CRITICAL HARD" * 10
        self.scheduler_loop(2, [[svc, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/HARD
        self.assertEqual('CRITICAL', svc.state)
        self.assertEqual('HARD', svc.state_type)

        # Should have a notification about it
        self.assert_any_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

        print "GO UNKNOWN HARD" * 10
        # Then we make it as a unknown state
        self.scheduler_loop(1, [[svc, 3, 'Unknown | value1=1 value2=2']])
        # And we DO NOT WANT A NOTIF HERE
        self.assert_no_log_match('SERVICE NOTIFICATION.*;UNKNOWN')
        self.show_and_clear_logs()

        print "Return CRITICAL HARD" * 10
        # Then we came back as WARNING here, so a different than we came in the phase!
        self.scheduler_loop(1, [[svc, 1, 'WARNING | value1=1 value2=2']])
        print svc.state, svc.state_type
        self.assert_any_log_match('SERVICE NOTIFICATION.*;WARNING')
        self.show_and_clear_logs()

        # We check if we can still have new notifications of course
        # And we speedup the notification
        for n in svc.notifications_in_progress.values():
            n.t_to_go = time.time()
        self.scheduler_loop(1, [[svc, 1, 'WARNING | value1=1 value2=2']])
        print svc.state, svc.state_type
        self.assert_any_log_match('SERVICE NOTIFICATION.*;WARNING')
        self.show_and_clear_logs()

        # And what if we came back as critical so? :)
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | value1=1 value2=2']])
        print svc.state, svc.state_type
        self.assert_any_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

    # But we want to still raise notif as unknown if we first met this state
    def test_unknown_still_raise_notif(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'OK | value1=0 value2=0']])
        self.assertEqual('OK', svc.state)
        self.assertEqual('HARD', svc.state_type)

        # Ok we are UP, now we seach to go in trouble
        self.scheduler_loop(1, [[svc, 3, 'PROBLEM | value1=1 value2=2']])
        # UNKOWN/SOFT
        self.assertEqual('UNKNOWN', svc.state)
        self.assertEqual('SOFT', svc.state_type)
        # And again and again :)
        self.scheduler_loop(2, [[svc, 3, 'PROBLEM | value1=1 value2=2']])
        # UNKNOWN/HARD
        self.assertEqual('UNKNOWN', svc.state)
        self.assertEqual('HARD', svc.state_type)

        # Should have a notification about it!
        self.assert_any_log_match('SERVICE NOTIFICATION.*;UNKNOWN')
        self.show_and_clear_logs()

        # Then we make it as a critical state
        # and we want a notif too
        self.scheduler_loop(1, [[svc, 2, 'critical | value1=1 value2=2']])
        self.assert_any_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

    # We got problem with unknown results on bad connections
    # for critical services and host: if it was in a notification pass
    # then the notification is restarted, but it's just a missing data,
    # not a reason to warn about it
    def test_unreach_do_not_change_state(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        print "GO OK" * 10
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'OK | value1=0 value2=0']])
        self.assertEqual('OK', svc.state)
        self.assertEqual('HARD', svc.state_type)

        print "GO DOWN SOFT" * 10
        # Ok we are UP, now we seach to go in trouble
        self.scheduler_loop(1, [[host, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/SOFT
        self.assertEqual('DOWN', host.state)
        self.assertEqual('SOFT', host.state_type)
        # And again and again :)
        print "GO CRITICAL HARD" * 10
        self.scheduler_loop(2, [[host, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/HARD
        self.assertEqual('DOWN', host.state)
        self.assertEqual('HARD', host.state_type)

        # Should have a notification about it
        self.assert_any_log_match('HOST NOTIFICATION.*;DOWN')
        self.show_and_clear_logs()

        print "GO UNREACH HARD" * 10
        # Then we make it as a unknown state
        self.scheduler_loop(3, [[router, 2, 'Bad router | value1=1 value2=2']])
        # so we warn about the router, not the host
        self.assert_any_log_match('HOST NOTIFICATION.*;DOWN')
        self.show_and_clear_logs()

        print "BIBI" * 100
        for n in host.notifications_in_progress.values():
            print n.__dict__

        # the we go in UNREACH
        self.scheduler_loop(1, [[host, 2, 'CRITICAL | value1=1 value2=2']])
        print host.state, host.state_type
        self.show_and_clear_logs()
        self.assertEqual('UNREACHABLE', host.state)
        self.assertEqual('HARD', host.state_type)

        # The the router came back :)
        print "Router is back from Hell" * 10
        self.scheduler_loop(1, [[router, 0, 'Ok, I am back guys | value1=1 value2=2']])
        self.assert_any_log_match('HOST NOTIFICATION.*;UP')
        self.show_and_clear_logs()

        # But how the host will say now?
        self.scheduler_loop(1, [[host, 2, 'CRITICAL | value1=1 value2=2']])
        print host.state, host.state_type
        # And here we DO NOT WANT new notification
        # If you follow, it THE important point of this test!
        self.assert_no_log_match('HOST NOTIFICATION.*;DOWN')
        self.show_and_clear_logs()

        print "Now go in the future, I want a notification"
        # Check if we still got the next notification for this of course

        # Hack so the notification will raise now if it can
        for n in host.notifications_in_progress.values():
            n.t_to_go = time.time()
        self.scheduler_loop(1, [[host, 2, 'CRITICAL | value1=1 value2=2']])
        print host.state, host.state_type
        # And here we DO NOT WANT new notification
        self.assert_any_log_match('HOST NOTIFICATION.*;DOWN')
        self.show_and_clear_logs()





if __name__ == '__main__':
    unittest.main()
