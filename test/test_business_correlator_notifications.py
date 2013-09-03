#!/usr/bin/env python
# Copyright (C) 2009-2010:
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
from shinken_test import unittest, ShinkenTest


class TestBusinesscorrelNotifications(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/nagios_business_correlator_notifications.cfg')

    def test_bprule_standard_notifications(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_default")
        svc_cor.act_depend_of = []
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.business_rule_smart_notifications is False)

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
        self.assert_(svc2.problem_has_been_acknowledged is True)

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])

        self.assert_(svc_cor.business_rule.get_state() == 2)
        self.assert_(svc_cor.notification_is_blocked_by_item('PROBLEM') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('ACKNOWLEDGEMENT') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('DOWNTIME') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('RECOVERY') is False)

    def test_bprule_smart_notifications_ack(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_smart_notif")
        svc_cor.act_depend_of = []
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.business_rule_smart_notifications is True)

        dummy = self.sched.hosts.find_by_name("dummy")
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        self.scheduler_loop(2, [
            [dummy, 0, 'UP dummy'],
            [svc1, 0, 'OK test_host_01/srv1'],
            [svc2, 2, 'CRITICAL test_host_02/srv2']], do_sleep=True)

        self.assert_(svc_cor.business_rule.get_state() == 2)
        self.assert_(svc_cor.notification_is_blocked_by_item('PROBLEM') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('ACKNOWLEDGEMENT') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('RECOVERY') is False)

        now = time.time()
        cmd = "[%lu] ACKNOWLEDGE_SVC_PROBLEM;test_host_02;srv2;2;1;1;lausser;blablub" % (now)
        self.sched.run_external_command(cmd)
        self.assert_(svc2.problem_has_been_acknowledged is True)

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])

        self.assert_(svc_cor.notification_is_blocked_by_item('PROBLEM') is True)
        self.assert_(svc_cor.notification_is_blocked_by_item('ACKNOWLEDGEMENT') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('RECOVERY') is False)

    def test_bprule_smart_notifications_ack_downtime(self):
        svc_cor = self.sched.services.find_srv_by_name_and_hostname("dummy", "bp_rule_smart_notif")
        svc_cor.act_depend_of = []
        self.assert_(svc_cor.got_business_rule is True)
        self.assert_(svc_cor.business_rule is not None)
        self.assert_(svc_cor.business_rule_smart_notifications is True)
        self.assert_(svc_cor.business_rule_downtime_as_ack is False)

        dummy = self.sched.hosts.find_by_name("dummy")
        svc1 = self.sched.services.find_srv_by_name_and_hostname("test_host_01", "srv1")
        svc2 = self.sched.services.find_srv_by_name_and_hostname("test_host_02", "srv2")

        self.scheduler_loop(2, [
            [dummy, 0, 'UP dummy'],
            [svc1, 0, 'OK test_host_01/srv1'],
            [svc2, 2, 'CRITICAL test_host_02/srv2']], do_sleep=True)

        self.assert_(svc_cor.business_rule.get_state() == 2)
        self.assert_(svc_cor.notification_is_blocked_by_item('PROBLEM') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('ACKNOWLEDGEMENT') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('DOWNTIME') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('RECOVERY') is False)

        duration = 600
        now = time.time()
        # fixed downtime valid for the next 10 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_02;srv2;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])
        self.assert_(svc2.scheduled_downtime_depth > 0)

        self.assert_(svc_cor.notification_is_blocked_by_item('PROBLEM') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('ACKNOWLEDGEMENT') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('DOWNTIME') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('RECOVERY') is False)

        svc_cor.business_rule_downtime_as_ack = True

        self.scheduler_loop(1, [[svc_cor, None, None]], do_sleep=True)
        self.scheduler_loop(1, [[svc_cor, None, None]])

        self.assert_(svc_cor.notification_is_blocked_by_item('PROBLEM') is True)
        self.assert_(svc_cor.notification_is_blocked_by_item('ACKNOWLEDGEMENT') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('DOWNTIME') is False)
        self.assert_(svc_cor.notification_is_blocked_by_item('RECOVERY') is False)

if __name__ == '__main__':
    unittest.main()
