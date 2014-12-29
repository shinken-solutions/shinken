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
#time.time = original_time_time
#time.sleep = original_time_sleep
from shinken.objects.timeperiod import Timeperiod


class TestMaintPeriod(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_maintenance_period.cfg')

    def test_check_defined_maintenance_period(self):
        a_24_7 = self.sched.timeperiods.find_by_name("24x7")
        print "Get the hosts and services"
        test_router_0 = self.sched.hosts.find_by_name("test_router_0")
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_nobody = self.sched.hosts.find_by_name("test_nobody")

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "test_ok_0")
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_nobody", "test_ok_0")

        # Standard links
        self.assertEqual(a_24_7, test_router_0.maintenance_period)
        self.assertIs(None, test_host_0.maintenance_period)
        self.assertIs(None, test_nobody.maintenance_period)

        # Now inplicit inheritance
        # This one is defined in the service conf
        self.assertEqual(a_24_7, svc1.maintenance_period)
        # And others are implicitly inherited
        self.assertIs(a_24_7, svc2.maintenance_period)
        # This one got nothing :)
        self.assertIs(None, svc3.maintenance_period)

    def test_check_enter_downtime(self):
        test_router_0 = self.sched.hosts.find_by_name("test_router_0")
        test_host_0 = self.sched.hosts.find_by_name("test_host_0")
        test_nobody = self.sched.hosts.find_by_name("test_nobody")

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_router_0", "test_ok_0")
        svc3 = self.sched.services.find_srv_by_name_and_hostname("test_nobody", "test_ok_0")
        # we want to focus on only one maintenance
        test_router_0.maintenance_period = None
        test_host_0.maintenance_period = None
        test_nobody.maintenance_period = None
        svc1.maintenance_period = None
        svc2.maintenance_period = None

        # be sure we have some time before a new minute begins.
        # otherwise we get a race condition and a failed test here.
        now = time.time()
        x = time.gmtime(now)
        while x.tm_sec < 50:
            time.sleep(1)
            now = time.time()
            x = time.gmtime(now)

        now = time.time()
        print "now it is", time.asctime(time.localtime(now))
        nowday = time.strftime("%A", time.localtime(now + 60)).lower()
        soonstart = time.strftime("%H:%M", time.localtime(now + 60))
        soonend = time.strftime("%H:%M", time.localtime(now + 180))

        range = "%s %s-%s" % (nowday, soonstart, soonend)
        print "range is ", range
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, range)
        t_next = t.get_next_valid_time_from_t(now)
        print "planned start", time.asctime(time.localtime(t_next))
        t_next = t.get_next_invalid_time_from_t(t_next + 1)
        print "planned stop ", time.asctime(time.localtime(t_next))
        svc3.maintenance_period = t

        self.assertFalse(svc3.in_maintenance)
        #
        # now let the scheduler run and wait until the maintenance period begins
        # it is now 10 seconds before the full minute. run for 30 seconds
        # in 1-second-intervals. this should be enough to trigger the downtime
        # in 10 seconds from now the downtime starts
        print "scheduler_loop start", time.asctime()
        self.scheduler_loop(30, [[svc3, 0, 'OK']], do_sleep=True, sleep_time=1)
        print "scheduler_loop end  ", time.asctime()

        self.assertTrue(hasattr(svc3, 'in_maintenance'))
        self.assertEqual(1, len(self.sched.downtimes))
        try:
            print "........................................."
            print self.sched.downtimes[1]
            print "downtime starts", time.asctime(self.sched.downtimes[1].start_time)
            print "downtime ends  ", time.asctime(self.sched.downtimes[1].end_time)
        except Exception:
            print "looks like there is no downtime"
            pass
        self.assertEqual(1, len(svc3.downtimes))
        self.assertIn(svc3.downtimes[0], self.sched.downtimes.values())
        self.assertTrue(svc3.in_scheduled_downtime)
        self.assertTrue(svc3.downtimes[0].fixed)
        self.assertTrue(svc3.downtimes[0].is_in_effect)
        self.assertFalse(svc3.downtimes[0].can_be_deleted)
        self.assertEqual(svc3.downtimes[0].id, svc3.in_maintenance)

        #
        # now the downtime should expire...
        # we already have 20 seconds (after 10 seconds of startup).
        # the downtime is 120 seconds long.
        # run the remaining 100 seconds plus 5 seconds just to be sure
        self.scheduler_loop(105, [[svc3, 0, 'OK']], do_sleep=True, sleep_time=1)

        self.assertEqual(0, len(self.sched.downtimes))
        self.assertEqual(0, len(svc3.downtimes))
        self.assertFalse(svc3.in_scheduled_downtime)
        self.assertIs(None, svc3.in_maintenance)



if __name__ == '__main__':
    unittest.main()
