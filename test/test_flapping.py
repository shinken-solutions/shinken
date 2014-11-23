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


class TestFlapping(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_flapping.cfg')

    def test_flapping(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        router = self.sched.hosts.find_by_name("test_router_0")
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 0, 'OK']])
        self.assertEqual('UP', host.state)
        self.assertEqual('HARD', host.state_type)
        self.assertTrue(svc.flap_detection_enabled)

        print 'A' * 41, svc.low_flap_threshold
        self.assertEqual(-1, svc.low_flap_threshold)

        # Now 1 test with a bad state
        self.scheduler_loop(1, [[svc, 2, 'Crit']])
        print "******* Current flap change lsit", svc.flapping_changes
        self.scheduler_loop(1, [[svc, 2, 'Crit']])
        print "****** Current flap change lsit", svc.flapping_changes
        # Ok, now go in flap!
        for i in xrange(1, 10):
            "**************************************************"
            print "I:", i
            self.scheduler_loop(1, [[svc, 0, 'Ok']])
            print "******* Current flap change lsit", svc.flapping_changes
            self.scheduler_loop(1, [[svc, 2, 'Crit']])
            print "****** Current flap change lsit", svc.flapping_changes
            print "In flapping?", svc.is_flapping

        # Should get in flapping now
        self.assertTrue(svc.is_flapping)
        # and get a log about it
        self.assert_any_log_match('SERVICE FLAPPING ALERT.*;STARTED')
        self.assert_any_log_match('SERVICE NOTIFICATION.*;FLAPPINGSTART')

        # Now we put it as back :)
        # 10 is not enouth to get back as normal
        for i in xrange(1, 11):
            self.scheduler_loop(1, [[svc, 0, 'Ok']])
            print "In flapping?", svc.is_flapping
        self.assertTrue(svc.is_flapping)

        # 10 others can be good (near 4.1 %)
        for i in xrange(1, 11):
            self.scheduler_loop(1, [[svc, 0, 'Ok']])
            print "In flapping?", svc.is_flapping
        self.assertFalse(svc.is_flapping)
        self.assert_any_log_match('SERVICE FLAPPING ALERT.*;STOPPED')
        self.assert_any_log_match('SERVICE NOTIFICATION.*;FLAPPINGSTOP')

        ############ Now get back in flap, and try the exteral commands change

        # Now 1 test with a bad state
        self.scheduler_loop(1, [[svc, 2, 'Crit']])
        print "******* Current flap change lsit", svc.flapping_changes
        self.scheduler_loop(1, [[svc, 2, 'Crit']])
        print "****** Current flap change lsit", svc.flapping_changes
        # Ok, now go in flap!
        for i in xrange(1, 10):
            "**************************************************"
            print "I:", i
            self.scheduler_loop(1, [[svc, 0, 'Ok']])
            print "******* Current flap change lsit", svc.flapping_changes
            self.scheduler_loop(1, [[svc, 2, 'Crit']])
            print "****** Current flap change lsit", svc.flapping_changes
            print "In flapping?", svc.is_flapping

        # Should get in flapping now
        self.assertTrue(svc.is_flapping)
        # and get a log about it
        self.assert_any_log_match('SERVICE FLAPPING ALERT.*;STARTED')
        self.assert_any_log_match('SERVICE NOTIFICATION.*;FLAPPINGSTART')

        # We run a globa lflap disable, so we should stop flapping now
        cmd = "[%lu] DISABLE_FLAP_DETECTION" % int(time.time())
        self.sched.run_external_command(cmd)

        self.assertFalse(svc.is_flapping)

        ############# NOW a local command for this service
        # First reenable flap:p
        cmd = "[%lu] ENABLE_FLAP_DETECTION" % int(time.time())
        self.sched.run_external_command(cmd)

        # Now 1 test with a bad state
        self.scheduler_loop(1, [[svc, 2, 'Crit']])
        print "******* Current flap change lsit", svc.flapping_changes
        self.scheduler_loop(1, [[svc, 2, 'Crit']])
        print "****** Current flap change lsit", svc.flapping_changes
        # Ok, now go in flap!
        for i in xrange(1, 10):
            "**************************************************"
            print "I:", i
            self.scheduler_loop(1, [[svc, 0, 'Ok']])
            print "******* Current flap change lsit", svc.flapping_changes
            self.scheduler_loop(1, [[svc, 2, 'Crit']])
            print "****** Current flap change lsit", svc.flapping_changes
            print "In flapping?", svc.is_flapping

        # Should get in flapping now
        self.assertTrue(svc.is_flapping)
        # and get a log about it
        self.assert_any_log_match('SERVICE FLAPPING ALERT.*;STARTED')
        self.assert_any_log_match('SERVICE NOTIFICATION.*;FLAPPINGSTART')

        # We run a globa lflap disable, so we should stop flapping now
        cmd = "[%lu] DISABLE_SVC_FLAP_DETECTION;test_host_0;test_ok_0" % int(time.time())
        self.sched.run_external_command(cmd)

        self.assertFalse(svc.is_flapping)




if __name__ == '__main__':
    unittest.main()
