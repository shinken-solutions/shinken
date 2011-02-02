#!/usr/bin/env python2.6
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *


class TestUnknownNotChangeState(ShinkenTest):
    #Uncomment this is you want to use a specific configuration
    #for your test
    #def setUp(self):
    #    self.setup_with_file('etc/nagios_1r_1h_1s.cfg')

    
    # We got problem with unknown results on bad connexions 
    # for critical services and host : if it was in a notification pass
    # then the notification is restarted, but it's just a missing data,
    # not a reason to warn about it
    def test_unknown_do_not_change_state(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'OK | value1=0 value2=0']])
        self.assert_(svc.state == 'OK')
        self.assert_(svc.state_type == 'HARD')

        # Ok we are UP, now we seach to go in trouble
        self.scheduler_loop(1, [[svc, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/SOFT
        self.assert_(svc.state == 'CRITICAL')
        self.assert_(svc.state_type == 'SOFT')
        # And again and again :)
        self.scheduler_loop(2, [[svc, 2, 'PROBLEM | value1=1 value2=2']])
        # CRITICAL/HARD
        self.assert_(svc.state == 'CRITICAL')
        self.assert_(svc.state_type == 'HARD')

        # Should have a notification about it
        self.assert_(self.any_log_match('SERVICE NOTIFICATION.*;CRITICAL'))
        self.show_and_clear_logs()

        # Then we make it as a unknown state
        self.scheduler_loop(1, [[svc, 3, 'Unknown | value1=1 value2=2']])
        self.assert_(self.any_log_match('SERVICE NOTIFICATION.*;UNKNOWN'))
        self.show_and_clear_logs()

        # Then we came back as CRITICAL
        self.scheduler_loop(1, [[svc, 2, 'CRITICAL | value1=1 value2=2']])
        print svc.state, svc.state_type
        self.assert_(self.any_log_match('SERVICE NOTIFICATION.*;CRITICAL'))
        self.show_and_clear_logs()



    # But we want to still raise notif as unknown if we first met this state
    def test_unknown_still_raise_notif(self):
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'OK | value1=0 value2=0']])
        self.assert_(svc.state == 'OK')
        self.assert_(svc.state_type == 'HARD')

        # Ok we are UP, now we seach to go in trouble
        self.scheduler_loop(1, [[svc, 3, 'PROBLEM | value1=1 value2=2']])
        # UNKOWN/SOFT
        self.assert_(svc.state == 'UNKNOWN')
        self.assert_(svc.state_type == 'SOFT')
        # And again and again :)
        self.scheduler_loop(2, [[svc, 3, 'PROBLEM | value1=1 value2=2']])
        # UNKNOWN/HARD
        self.assert_(svc.state == 'UNKNOWN')
        self.assert_(svc.state_type == 'HARD')

        # Should have a notification about it !
        self.assert_(self.any_log_match('SERVICE NOTIFICATION.*;UNKNOWN'))
        self.show_and_clear_logs()

        # Then we make it as a critical state
        # and we want a notif too
        self.scheduler_loop(1, [[svc, 2, 'critical | value1=1 value2=2']])
        self.assert_(self.any_log_match('SERVICE NOTIFICATION.*;CRITICAL'))
        self.show_and_clear_logs()


        


if __name__ == '__main__':
    unittest.main()

