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


class TestConfig(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_obsess.cfg')

    def test_ocsp(self):
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
        self.assertTrue(svc.obsess_over_service)
        self.assertTrue(svc.__class__.obsess_over)
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual(1, self.count_actions())
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual(1, self.count_actions())

        now = time.time()
        cmd = "[%lu] STOP_OBSESSING_OVER_SVC;test_host_0;test_ok_0" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assertFalse(svc.obsess_over_service)
        self.assertTrue(svc.__class__.obsess_over)
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual(0, self.count_actions())
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual(0, self.count_actions())

        now = time.time()
        cmd = "[%lu] START_OBSESSING_OVER_SVC;test_host_0;test_ok_0" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assertTrue(svc.obsess_over_service)
        self.assertTrue(svc.__class__.obsess_over)
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual(1, self.count_actions())
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assertEqual(1, self.count_actions())

        now = time.time()
        cmd = "[%lu] START_OBSESSING_OVER_SVC_CHECKS" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assertTrue(svc.obsess_over_service)
        self.assertTrue(svc.__class__.obsess_over)

        now = time.time()
        cmd = "[%lu] STOP_OBSESSING_OVER_SVC_CHECKS" % now
        self.sched.run_external_command(cmd)
        self.sched.get_new_actions()
        self.worker_loop()
        self.assertTrue(svc.obsess_over_service)
        self.assertFalse(svc.__class__.obsess_over)

    def test_ochp(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'OK']])
        self.show_actions()
        self.assertEqual(1, self.count_actions())
        self.scheduler_loop(1, [[router, 0, 'OK']])
        self.show_actions()
        print "host", host.obsess_over
        print "rout", router.obsess_over
        print "host", host.obsess_over_host
        print "rout", router.obsess_over_host
        self.assertEqual(0, self.count_actions())
        self.assertTrue(host.obsess_over_host)
        self.assertFalse(router.obsess_over_host)
        # the router does not obsess (host definition)
        # but it's class does (shinken.cfg)
        self.assertTrue(router.__class__.obsess_over)


if __name__ == '__main__':
    unittest.main()
