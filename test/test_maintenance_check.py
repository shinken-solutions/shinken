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
# This file is used to test object properties overriding.
#

from __future__ import absolute_import, division, print_function, unicode_literals

from shinken_test import unittest, ShinkenTest, time
from shinken.objects.timeperiod import Timeperiod
import re


class TestMaintenaceCheck(ShinkenTest):

    def setUp(self):
        self.setup_with_file("etc/shinken_maintenance_check.cfg")

    def check_object_status(self, obj, wanted_downtime, wanted_notifications):
        self.assertIs(obj.in_scheduled_downtime, wanted_downtime)
        if wanted_downtime is True:
            self.assertTrue(obj.in_scheduled_downtime)
            self.assertTrue(obj.scheduled_downtime_depth > 0)
            self.assertIsNotNone(obj.in_maintenance)
        else:
            self.assertFalse(obj.in_scheduled_downtime)
            self.assertTrue(obj.scheduled_downtime_depth == 0)
            self.assertIsNone(obj.in_maintenance)

        if wanted_notifications is True:
            self.assertFalse(obj.notification_is_blocked_by_item("PROBLEM"))
        else:
            self.assertTrue(obj.notification_is_blocked_by_item("PROBLEM"))

    def test_maintenance_check(self):
        period = self.sched.timeperiods.find_by_name("24x7")
        hst1 = self.sched.hosts.find_by_name("test_host_1")
        hst2 = self.sched.hosts.find_by_name("test_host_2")
        svc11 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_service_1")
        svc12 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_service_2")
        svc21 = self.sched.services.find_srv_by_name_and_hostname("test_host_2", "test_service_1")
        svc22 = self.sched.services.find_srv_by_name_and_hostname("test_host_2", "test_service_2")

        # Tests objets are correctly configurred
        self.assertIsNotNone(hst1)
        self.assertIsNone(hst1.maintenance_check_period)

        self.assertIsNotNone(hst2)
        self.assertIs(hst2.maintenance_check_period, period)

        self.assertIsNotNone(svc11)
        self.assertIsNone(svc11.maintenance_check_period)

        self.assertIsNotNone(svc12)
        self.assertIs(svc12.maintenance_check_period, period)

        self.assertIsNotNone(svc21)
        self.assertIsNone(svc21.maintenance_check_period)

        self.assertIsNotNone(svc22)
        self.assertIs(svc22.maintenance_check_period, period)

        # Run standard checks
        self.scheduler_loop(2, [
            {
                "item": hst1,
                "exit_status": 0,
                "output": "UP test_host_1"
            },
            {
                "item": hst2,
                "exit_status": 0,
                "output": "UP test_host_2"
            },
            {
                "item": svc11,
                "exit_status": 0,
                "output": "OK test_host_1/test_service_1"
            },
            {
                "item": svc12,
                "exit_status": 0,
                "output": "OK test_host_1/test_service_2"
            },
            {
                "item": svc21,
                "exit_status": 0,
                "output": "OK test_host_2/test_service_1"
            },
            {
                "item": svc22,
                "exit_status": 0,
                "output": "OK test_host_2/test_service_2"
            },
        ])

        # Tests objets state
        self.check_object_status(hst1, False, True)
        self.check_object_status(hst2, False, True)
        self.check_object_status(svc11, False, True)
        self.check_object_status(svc12, False, True)
        self.check_object_status(svc21, False, True)
        self.check_object_status(svc22, False, True)

        # Run maintenance check (disabled)
        self.scheduler_loop(1, [
            {
                "item": hst2,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc12,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_1/test_service_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc22,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
        ])

        # Tests objets state
        self.check_object_status(hst1, False, True)
        self.check_object_status(hst2, True, False)
        self.check_object_status(svc11, False, True)
        self.check_object_status(svc12, True, False)
        # hst2 is under downtime, so svc21 has notifications disabled
        self.check_object_status(svc21, False, False)
        self.check_object_status(svc22, True, False)

        # Run maintenance check (back to production)
        self.scheduler_loop(1, [
            {
                "item": hst2,
                "exit_status": 0,
                "output": "PRODUCTION test_host_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc12,
                "exit_status": 0,
                "output": "PRODUCTION test_host_1/test_service_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc22,
                "exit_status": 0,
                "output": "PRODUCTION test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
        ])

        self.check_object_status(hst1, False, True)
        self.check_object_status(hst2, False, True)
        self.check_object_status(svc11, False, True)
        self.check_object_status(svc12, False, True)
        self.check_object_status(svc21, False, True)
        self.check_object_status(svc22, False, True)

    def test_maintenance_check_timeout(self):
        hst1 = self.sched.hosts.find_by_name("test_host_1")
        hst2 = self.sched.hosts.find_by_name("test_host_2")
        svc12 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_service_2")
        svc22 = self.sched.services.find_srv_by_name_and_hostname("test_host_2", "test_service_2")

        self.scheduler_loop(2, [
            {
                "item": hst1,
                "exit_status": 0,
                "output": "OK test_host_1"
            },
            {
                "item": hst2,
                "exit_status": 0,
                "output": "OK test_host_1"
            },
            {
                "item": svc12,
                "exit_status": 0,
                "output": "OK test_host_1/test_service_2"
            },
            {
                "item": svc22,
                "exit_status": 0,
                "output": "OK test_host_2/test_service_2"
            },
        ])

        # Run maintenance check (two are timed out)
        self.scheduler_loop(1, [
            {
                "item": svc12,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_1/test_service_2",
                "check_variant": "maintenance",
                "timeout": True,
            },
            {
                "item": svc22,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2/test_service_2",
                "check_variant": "maintenance",
            },
        ])
        # Tests objets state
        self.check_object_status(svc12, False, True)
        self.check_object_status(svc22, True, False)

    def test_maintenance_period_check_overlap(self):
        hst2 = self.sched.hosts.find_by_name("test_host_2")
        svc22 = self.sched.services.find_srv_by_name_and_hostname("test_host_2", "test_service_2")

        # be sure we have some time before a new minute begins.
        # otherwise we get a race condition and a failed test here.
        now = time.time()
        x = time.gmtime(now)
        while x.tm_sec < 50:
            time.sleep(1)
            now = time.time()
            x = time.gmtime(now)

        now = time.time()
        start_tuple = time.localtime(now + 60)
        nowday = time.strftime("%A", start_tuple).lower()
        soonstart = time.strftime("%H:%M", start_tuple)
        end_tuple = time.localtime(now + 180)
        soonend = time.strftime("%H:%M", end_tuple)

        dt_range = "%s %s-%s" % (nowday, soonstart, soonend)
        t = Timeperiod()
        t.timeperiod_name = ""
        t.resolve_daterange(t.dateranges, dt_range)
        t_start = t.get_next_valid_time_from_t(now)
        t_end = t.get_next_invalid_time_from_t(t_start + 1) - 1
        hst2.maintenance_period = t
        svc22.maintenance_period = t

        self.assertIsNone(hst2.in_maintenance)
        self.assertIsNone(svc22.in_maintenance)

        # Run maintenance check (out of production)
        self.scheduler_loop(1, [
            {
                "item": hst2,
                "exit_status": 0,
                "output": "UP test_host_2"
            },
            {
                "item": svc22,
                "exit_status": 0,
                "output": "OK test_host_2/test_service_2"
            },
            {
                "item": hst2,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc22,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
        ])

        # Downtimes are created because of maintenance check result
        self.check_object_status(hst2, True, False)
        self.check_object_status(svc22, True, False)
        self.assertEqual(len(self.sched.downtimes), 2)
        self.assertIn(hst2.downtimes[0], self.sched.downtimes.values())
        self.assertIn(svc22.downtimes[0], self.sched.downtimes.values())
        hst2_dt_id = hst2.downtimes[0].id
        self.assertEqual(hst2_dt_id, hst2.in_maintenance)
        svc22_dt_id = svc22.downtimes[0].id
        self.assertEqual(svc22_dt_id, svc22.in_maintenance)
        self.assertLess(hst2.downtimes[0].end_time, t_end)
        self.assertLess(svc22.downtimes[0].end_time, t_end)

        # now let the scheduler run and wait until the maintenance period begins
        # it is now 10 seconds before the full minute. run for 30 seconds
        # in 1-second-intervals. this should be enough to trigger the downtime
        # in 10 seconds from now the downtime starts
        self.scheduler_loop(30, [
            {
                "item": hst2,
                "exit_status": 0,
                "output": "UP test_host_2"
            },
            {
                "item": svc22,
                "exit_status": 0,
                "output": "OK test_host_2/test_service_2"
            },
            {
                "item": hst2,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc22,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
        ], do_sleep=True, sleep_time=1)

        # Downtimes are set from maintenance period, which has precedence
        self.check_object_status(hst2, True, False)
        self.check_object_status(svc22,True, False)
        self.assertEqual(len(self.sched.downtimes), 2)
        self.assertIn(hst2.downtimes[0], self.sched.downtimes.values())
        self.assertIn(svc22.downtimes[0], self.sched.downtimes.values())
        self.assertEqual(hst2_dt_id, hst2.in_maintenance)
        self.assertEqual(svc22_dt_id, svc22.in_maintenance)
        self.assertEqual(hst2.downtimes[0].end_time, t_end)
        self.assertEqual(svc22.downtimes[0].end_time, t_end)

        #time.sleep(180)
        self.scheduler_loop(180, [
            {
                "item": hst2,
                "exit_status": 0,
                "output": "UP test_host_2"
            },
            {
                "item": svc22,
                "exit_status": 0,
                "output": "OK test_host_2/test_service_2"
            },
            {
                "item": hst2,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc22,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
        ], do_sleep=True, sleep_time=1)

        # Maintenace period has expired, downtimes are extended because of
        # maintenance check result
        self.check_object_status(hst2, True, False)
        self.check_object_status(svc22, True, False)
        self.assertEqual(len(self.sched.downtimes), 2)
        self.assertIn(hst2.downtimes[0], self.sched.downtimes.values())
        self.assertIn(svc22.downtimes[0], self.sched.downtimes.values())
        self.assertEqual(hst2_dt_id, hst2.in_maintenance)
        self.assertEqual(svc22_dt_id, svc22.in_maintenance)
        self.assertGreater(hst2.downtimes[0].end_time, t_end)
        self.assertGreater(svc22.downtimes[0].end_time, t_end)

    def test_maintenance_check_errors(self):
        hst1 = self.sched.hosts.find_by_name("test_host_1")
        hst2 = self.sched.hosts.find_by_name("test_host_2")
        svc12 = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_service_2")
        svc22 = self.sched.services.find_srv_by_name_and_hostname("test_host_2", "test_service_2")

        self.scheduler_loop(2, [
            {
                "item": hst1,
                "exit_status": 0,
                "output": "UP test_host_1"
            },
            {
                "item": hst2,
                "exit_status": 0,
                "output": "UP test_host_2"
            },
            {
                "item": svc12,
                "exit_status": 0,
                "output": "OK test_host_1/test_service_2"
            },
            {
                "item": svc22,
                "exit_status": 0,
                "output": "OK test_host_2/test_service_2"
            },
        ])
        self.scheduler_loop(1, [
            {
                "item": hst2,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc12,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc22,
                "exit_status": 2,
                "output": "MAINTENANCE test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
        ], do_sleep=True, sleep_time=1)

        self.scheduler_loop(1, [
            {
                "item": hst2,
                "exit_status": 1,
                "output": "invalid command test_host_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc12,
                "exit_status": 3,
                "output": "unknown option test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
            {
                "item": svc22,
                "exit_status": 5,
                "output": "bad hostname test_host_2/test_service_2",
                "check_variant": "maintenance"
            },
        ], do_sleep=True, sleep_time=1)

        # Get the arbiter's log broks
        #[b.prepare() for b in self.broks]
        logs = [b.data['log'] for b in self.broks if b.type == 'log']
        self.assertEqual(3, len([log for log in logs if re.search('got an invalid return code', log)]))

        # Invalid returcode should get the item back to production state
        self.check_object_status(hst2, False, True)
        self.check_object_status(svc12, False, True)
        self.check_object_status(svc22, False, True)

if __name__ == "__main__":
    unittest.main()
