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
# This file is used to test business rules smart notifications behaviour.
#

import time
from shinken_test import unittest, ShinkenTest, time_hacker


class TestBusinesscorrelNotifications(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_business_correlator_notifications.cfg')

    def test_bprule_standard_notifications(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_default")
        svc_cor.act_depend_of = []
        self.assertIs(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        self.assertIs(False, svc_cor.business_rule_smart_notifications)

        dummy = self.sched.hosts.find_by_name("dummy")
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        self.scheduler_loop(2, [
            [dummy, 0, 'UP dummy'],
            [svc1, 0, 'OK test_host_01/srv1'],
            [svc2, 2, 'CRITICAL test_host_02/srv2']], do_sleep=True)

        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_02;srv2;2;1;1;lausser;blablub" % (now)
        self.sched.run_external_command(cmd)
        self.assertIs(True, svc2.problem_has_been_acknowledged)

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])

        self.assertEqual(2, svc_cor.business_rule.get_state())
        self.assertIs(False, svc_cor.notification_is_blocked_by_item('PROBLEM'))

    def test_bprule_smart_notifications_ack(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_smart_notif")
        svc_cor.act_depend_of = []
        self.assertIs(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        self.assertIs(True, svc_cor.business_rule_smart_notifications)

        dummy = self.sched.hosts.find_by_name("dummy")
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        self.scheduler_loop(2, [
            [dummy, 0, 'UP dummy'],
            [svc1, 0, 'OK test_host_01/srv1'],
            [svc2, 2, 'CRITICAL test_host_02/srv2']], do_sleep=True)

        self.assertEqual(2, svc_cor.business_rule.get_state())
        self.assertIs(False, svc_cor.notification_is_blocked_by_item('PROBLEM'))

        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_02;srv2;2;1;1;lausser;blablub" % (now)
        self.sched.run_external_command(cmd)
        self.assertIs(True, svc2.problem_has_been_acknowledged)

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])

        self.assertIs(True, svc_cor.notification_is_blocked_by_item('PROBLEM'))

    def test_bprule_smart_notifications_svc_ack_downtime(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_smart_notif")
        svc_cor.act_depend_of = []
        self.assertIs(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        self.assertIs(True, svc_cor.business_rule_smart_notifications)
        self.assertIs(False, svc_cor.business_rule_downtime_as_ack)

        dummy = self.sched.hosts.find_by_name("dummy")
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        self.scheduler_loop(2, [
            [dummy, 0, 'UP dummy'],
            [svc1, 0, 'OK test_host_01/srv1'],
            [svc2, 2, 'CRITICAL test_host_02/srv2']], do_sleep=True)

        self.assertEqual(2, svc_cor.business_rule.get_state())
        self.assertIs(False, svc_cor.notification_is_blocked_by_item('PROBLEM'))

        duration = 600
        now = time.time()
        # fixed downtime valid for the next 10 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_02;srv2;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])
        self.assertGreater(svc2.scheduled_downtime_depth, 0)

        self.assertIs(False, svc_cor.notification_is_blocked_by_item('PROBLEM'))

        svc_cor.business_rule_downtime_as_ack = True

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])

        self.assertIs(True, svc_cor.notification_is_blocked_by_item('PROBLEM'))

    def test_bprule_smart_notifications_hst_ack_downtime(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_smart_notif")
        svc_cor.act_depend_of = []
        self.assertIs(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)
        self.assertIs(True, svc_cor.business_rule_smart_notifications)
        self.assertIs(False, svc_cor.business_rule_downtime_as_ack)

        dummy = self.sched.hosts.find_by_name("dummy")
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")
        hst2 = self.sched.hosts.find_by_name("test_host_02")

        self.scheduler_loop(2, [
            [dummy, 0, 'UP dummy'],
            [svc1, 0, 'OK test_host_01/srv1'],
            [svc2, 2, 'CRITICAL test_host_02/srv2']], do_sleep=True)

        self.assertEqual(2, svc_cor.business_rule.get_state())
        self.assertIs(False, svc_cor.notification_is_blocked_by_item('PROBLEM'))

        duration = 600
        now = time.time()
        # fixed downtime valid for the next 10 minutes
        cmd = "[%lu] SCHEDULE_HOST_DOWNTIME;test_host_02;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])
        self.assertGreater(hst2.scheduled_downtime_depth, 0)

        self.assertIs(False, svc_cor.notification_is_blocked_by_item('PROBLEM'))

        svc_cor.business_rule_downtime_as_ack = True

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])

        self.assertIs(True, svc_cor.notification_is_blocked_by_item('PROBLEM'))

    def test_bprule_child_notification_options(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_child_notif")
        svc_cor.act_depend_of = []
        self.assertIs(True, svc_cor.got_business_rule)
        self.assertIsNot(svc_cor.business_rule, None)

        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        hst2 = self.sched.hosts.find_by_name("test_host_02")

        self.assertEqual(['w', 'u', 'c', 'r', 's'], svc1.notification_options)
        self.assertEqual(['d', 'u', 'r', 's'], hst2.notification_options)

if __name__ == '__main__':
    unittest.main()
