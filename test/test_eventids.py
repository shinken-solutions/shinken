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
# This file is used to test current_event_id, last_event_id,
# current_problem_id and last_problem_id which are used for
# $HOSTEVENTID$, $HOSTPROBLEMID$ etc.
#

from shinken_test import *
from shinken.objects.schedulingitem import SchedulingItem


class TestConfig(ShinkenTest):

    def print_ids(self, host, svc, router):
        print "global: cei,lei,cpi,lpi = %d,%d" % (SchedulingItem.current_event_id, SchedulingItem.current_problem_id)
        print "service: cei,lei,cpi,lpi = %d,%d,%d,%d" % (svc.current_event_id, svc.last_event_id, svc.current_problem_id, svc.last_problem_id)
        print "host:    cei,lei,cpi,lpi = %d,%d,%d,%d" % (host.current_event_id, host.last_event_id, host.current_problem_id, host.last_problem_id)
        print "router:  cei,lei,cpi,lpi = %d,%d,%d,%d" % (router.current_event_id, router.last_event_id, router.current_problem_id, router.last_problem_id)

    def test_global_counters(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router

        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # This may be truc when running all Shinken test in the same "context" like
        # nosetest does. If you run this test alone, it will be 0.
        if SchedulingItem.current_event_id > 0 or  SchedulingItem.current_problem_id > 0:
            SchedulingItem.current_event_id = 0
            SchedulingItem.current_problem_id = 0

        self.print_ids(host, svc, router)
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=False)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(0, svc.current_event_id)
        self.assertEqual(0, svc.last_event_id)
        self.assertEqual(0, svc.current_problem_id)
        self.assertEqual(0, svc.last_problem_id)
        #--------------------------------------------------------------
        # service reaches soft;1
        # svc: 1,0,1,0
        #--------------------------------------------------------------
        print "- 1 x BAD get soft -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(1, svc.current_event_id)
        self.assertEqual(0, svc.last_event_id)
        self.assertEqual(1, svc.current_problem_id)
        self.assertEqual(0, svc.last_problem_id)
        #--------------------------------------------------------------
        # service reaches hard;2
        # svc: 1,0,1,0
        #--------------------------------------------------------------
        print "- 1 x BAD get hard -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(1, svc.current_event_id)
        self.assertEqual(0, svc.last_event_id)
        self.assertEqual(1, svc.current_problem_id)
        self.assertEqual(0, svc.last_problem_id)
        print "- 5 x BAD repeat -------------------------------------"
        self.scheduler_loop(5, [[svc, 2, 'BAD']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(1, svc.current_event_id)
        self.assertEqual(0, svc.last_event_id)
        self.assertEqual(1, svc.current_problem_id)
        self.assertEqual(0, svc.last_problem_id)
        #--------------------------------------------------------------
        # now recover.
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(2, svc.current_event_id)
        self.assertEqual(1, svc.last_event_id)
        self.assertEqual(0, svc.current_problem_id)
        self.assertEqual(1, svc.last_problem_id)
        #--------------------------------------------------------------
        # service fails again, ok->w->c
        #--------------------------------------------------------------
        print "- 4 x BAD get hard with non-ok statechange -------------"
        self.scheduler_loop(2, [[svc, 1, 'BAD']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(3, svc.current_event_id)
        self.assertEqual(2, svc.last_event_id)
        self.assertEqual(2, svc.current_problem_id)
        self.assertEqual(0, svc.last_problem_id)
        # another statechange
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(4, svc.current_event_id)
        self.assertEqual(3, svc.last_event_id)
        self.assertEqual(2, svc.current_problem_id)
        self.assertEqual(0, svc.last_problem_id)
        #--------------------------------------------------------------
        # now recover.
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(5, svc.current_event_id)
        self.assertEqual(4, svc.last_event_id)
        self.assertEqual(0, svc.current_problem_id)
        self.assertEqual(2, svc.last_problem_id)
        #--------------------------------------------------------------
        # mix in  two hosts
        #--------------------------------------------------------------
        print "- 4 x BAD get hard with non-ok statechange -------------"
        self.scheduler_loop(2, [[router, 2, 'DOWN']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(6, SchedulingItem.current_event_id)
        self.assertEqual(3, SchedulingItem.current_problem_id)
        self.assertEqual(0, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(0, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(5, svc.current_event_id)
        self.assertEqual(4, svc.last_event_id)
        self.assertEqual(0, svc.current_problem_id)
        self.assertEqual(2, svc.last_problem_id)
        self.assertEqual(6, router.current_event_id)
        self.assertEqual(0, router.last_event_id)
        self.assertEqual(3, router.current_problem_id)
        self.assertEqual(0, router.last_problem_id)
        # add chaos
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=False)
        self.scheduler_loop(2, [[router, 0, 'UP']], do_sleep=False)
        self.scheduler_loop(5, [[host, 2, 'DOWN']], do_sleep=False)
        self.print_ids(host, svc, router)
        self.assertEqual(9, SchedulingItem.current_event_id)
        self.assertEqual(5, SchedulingItem.current_problem_id)
        self.assertEqual(9, host.current_event_id)
        self.assertEqual(0, host.last_event_id)
        self.assertEqual(5, host.current_problem_id)
        self.assertEqual(0, host.last_problem_id)
        self.assertEqual(7, svc.current_event_id)
        self.assertEqual(5, svc.last_event_id)
        self.assertEqual(4, svc.current_problem_id)
        self.assertEqual(0, svc.last_problem_id)
        self.assertEqual(8, router.current_event_id)
        self.assertEqual(6, router.last_event_id)
        self.assertEqual(0, router.current_problem_id)
        self.assertEqual(3, router.last_problem_id)


if __name__ == '__main__':
    unittest.main()
