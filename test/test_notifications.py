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
# This file is used to test host- and service-downtimes.
#

import time

from shinken_test import unittest, ShinkenTest
from shinken_test import time_hacker


class TestNotif(ShinkenTest):

    def test_continuous_notifications(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

        # To make tests quicker we make notifications send very quickly
        svc.notification_interval = 0.001

        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)

        self.assertEqual(0, svc.current_notification_number)
        #--------------------------------------------------------------
        # service reaches soft;1
        # there must not be any notification
        #--------------------------------------------------------------
        print "- 1 x BAD get soft -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        # check_notification: not (soft)
        print "---current_notification_number", svc.current_notification_number
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created
        # notification number must be 1
        #--------------------------------------------------------------
        print "- 1 x BAD get hard -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        #self.show_and_clear_actions()
        self.show_actions()
        print svc.notifications_in_progress
        for n in svc.notifications_in_progress.values():
            print n
        # check_notification: yes (hard)
        print "---current_notification_number", svc.current_notification_number
        # notification_number is already sent. the next one has been scheduled
        # and is waiting for notification_interval to pass. so the current
        # number is 2
        self.assertEqual(1, svc.current_notification_number)
        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 5 x BAD repeat -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "cnn and cur", cnn, svc.current_notification_number
        self.assertGreater(svc.current_notification_number, cnn)
        cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "svc.current_notification_number, cnn", svc.current_notification_number, cnn
        self.assertGreater(svc.current_notification_number, cnn)
        #--------------------------------------------------------------
        # 2 cycles = 2 minutes = 2 new notifications
        #--------------------------------------------------------------
        cnn = svc.current_notification_number
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "svc.current_notification_number, cnn", svc.current_notification_number, cnn
        self.assertGreater(svc.current_notification_number, cnn)
        #--------------------------------------------------------------
        # 2 cycles = 2 minutes = 2 new notifications (theoretically)
        # BUT: test_contact filters notifications
        # we do not raise current_notification_number if no mail was sent
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] DISABLE_CONTACT_SVC_NOTIFICATIONS;test_contact" % now
        self.sched.run_external_command(cmd)
        cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        self.assertEqual(cnn, svc.current_notification_number)
        #--------------------------------------------------------------
        # again a normal cycle
        # test_contact receives his mail
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] ENABLE_CONTACT_SVC_NOTIFICATIONS;test_contact" % now
        self.sched.run_external_command(cmd)
        #cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "svc.current_notification_number, cnn", svc.current_notification_number, cnn
        self.assertEqual(cnn + 1, svc.current_notification_number)
        #--------------------------------------------------------------
        # now recover. there must be no scheduled/inpoller notification
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assertEqual(0, svc.current_notification_number)

    def test_continuous_notifications_delayed(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

        # To make tests quicker we make notifications send very quickly
        svc.notification_interval = 0.001  # and send imediatly then

        svc.first_notification_delay = 0.1  # set 6s for first notif delay
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=1)
        #-----------------------------------------------------------------
        # initialize with a good check. there must be no pending notification
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=1)
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assertEqual(0, svc.current_notification_number)
        #-----------------------------------------------------------------
        # check fails and enters soft state.
        # there must be no notification, only the event handler
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 1, 'BAD']], do_sleep=True, sleep_time=1)
        self.assertEqual(1, self.count_actions())
        now = time.time()
        print svc.last_time_warning, svc.last_time_critical, svc.last_time_unknown, svc.last_time_ok
        last_time_not_ok = svc.last_time_non_ok_or_up()
        deadline = svc.last_time_non_ok_or_up() + svc.first_notification_delay * svc.__class__.interval_length
        print("deadline is in %s secs" % (deadline - now))
        #-----------------------------------------------------------------
        # check fails again and enters hard state.
        # now there is a (scheduled for later) notification and an event handler
        # current_notification_number is still 0, until notifications
        # have actually been sent
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        self.assertEqual(0, svc.current_notification_number)
        # sleep up to deadline:
        time_hacker.time_warp(deadline - now)
        # even if time_hacker is used here, we still call time.sleep()
        # to show that we must wait the necessary delay time:
        time.sleep(deadline - now)
        #-----------------------------------------------------------------
        # now the delay period is over and the notification can be sent
        # with the next bad check
        # there is 1 action, the notification (
        # 1 notification was sent, so current_notification_number is 1
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=1)
        print "Counted actions", self.count_actions()
        self.assertEqual(2, self.count_actions())
        # 1 master, 1 child
        self.assertEqual(1, svc.current_notification_number)
        self.show_actions()
        self.assertEqual(1, len(svc.notifications_in_progress))  # master is zombieand removed_from_in_progress
        self.show_logs()
        self.assert_log_match(1, 'SERVICE NOTIFICATION.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()
        #-----------------------------------------------------------------
        # relax with a successful check
        # there are 2 actions, one notification and one eventhandler
        # current_notification_number was reset to 0
        #-----------------------------------------------------------------
        self.scheduler_loop(2, [[svc, 0, 'GOOD']], do_sleep=True, sleep_time=1)
        self.assert_log_match(1, 'SERVICE ALERT.*;OK;')
        self.assert_log_match(2, 'SERVICE EVENT HANDLER.*;OK;')
        self.assert_log_match(3, 'SERVICE NOTIFICATION.*;OK;')
        # evt reap 2 loops
        self.assertEqual(0, svc.current_notification_number)
        self.assertEqual(0, len(svc.notifications_in_progress))
        self.assertEqual(0, len(svc.notified_contacts))
        #self.assertEqual(2, self.count_actions())
        self.show_and_clear_logs()
        self.show_and_clear_actions()

    def test_continuous_notifications_delayed_recovers_fast(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.first_notification_delay = 5
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        #-----------------------------------------------------------------
        # initialize with a good check. there must be no pending notification
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assertEqual(0, svc.current_notification_number)
        #-----------------------------------------------------------------
        # check fails and enters soft state.
        # there must be no notification, only the event handler
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 1, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        self.assertEqual(1, self.count_actions())
        #-----------------------------------------------------------------
        # check fails again and enters hard state.
        # now there is a (scheduled for later) notification and an event handler
        # current_notification_number is still 0 (will be raised when
        # a notification is actually sent)
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        self.assertEqual(2, self.count_actions())
        self.assertEqual(0, svc.current_notification_number)
        #-----------------------------------------------------------------
        # repeat bad checks during the delay time
        # but only one time. we don't want to reach the deadline
        # there is one action: the pending notification
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        self.assertEqual(1, self.count_actions())
        #-----------------------------------------------------------------
        # relax with a successful check
        # there is 1 action, the eventhandler.
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']], do_sleep=True, sleep_time=0.1)
        self.assert_log_match(1, 'SERVICE ALERT.*;OK;')
        self.assert_log_match(2, 'SERVICE EVENT HANDLER.*;OK;')
        self.assert_log_match(3, 'SERVICE NOTIFICATION.*;OK;',
                              no_match=True)
        self.show_actions()
        self.assertEqual(0, len(svc.notifications_in_progress))
        self.assertEqual(0, len(svc.notified_contacts))
        self.assertEqual(1, self.count_actions())
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def test_host_in_downtime_or_down_service_critical(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

        # To make tests quicker we make notifications send very quickly
        svc.notification_interval = 0.001

        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP'], [svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.assertEqual(0, svc.current_notification_number)
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created
        # notification number must be 1
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[host, 0, 'UP'], [svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_logs()
        self.show_actions()
        self.assert_log_match(1, 'SERVICE ALERT.*;CRITICAL;SOFT')
        self.assert_log_match(2, 'SERVICE EVENT HANDLER.*;CRITICAL;SOFT')
        self.assert_log_match(3, 'SERVICE ALERT.*;CRITICAL;HARD')
        self.assert_log_match(4, 'SERVICE EVENT HANDLER.*;CRITICAL;HARD')
        self.assert_log_match(5, 'SERVICE NOTIFICATION.*;CRITICAL;')
        self.assertEqual(1, svc.current_notification_number)
        self.clear_logs()
        self.clear_actions()
        #--------------------------------------------------------------
        # reset host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP'], [svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.assertEqual(0, svc.current_notification_number)
        duration = 300
        now = time.time()
        # fixed downtime valid for the next 5 minutes
        cmd = "[%lu] SCHEDULE_HOST_DOWNTIME;test_host_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        #--------------------------------------------------------------
        # service reaches hard;2
        # no notificatio
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[host, 0, 'UP'], [svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('HOST NOTIFICATION.*;DOWNTIMESTART')
        self.assert_no_log_match('SERVICE NOTIFICATION.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_and_clear_actions()

    def test_only_notified_contacts_notifications(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

        # To make tests quicker we make notifications send very quickly
        svc.notification_interval = 0.001

        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # We want the contact to do not have a mail, so we remove tyhe 'u'
        test_contact = self.sched.contacts.find_by_name('test_contact')
        for nw in test_contact.notificationways:
            nw.service_notification_options.remove('u')

        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)

        self.assertEqual(0, svc.current_notification_number)
        #--------------------------------------------------------------
        # service reaches soft;1
        # there must not be any notification
        #--------------------------------------------------------------
        print "- 1 x BAD get soft -------------------------------------"
        self.scheduler_loop(1, [[svc, 3, 'UNKNOWN']], do_sleep=True, sleep_time=0.1)
        # check_notification: not (soft)
        print "---current_notification_number", svc.current_notification_number
        print "Contact we notified", svc.notified_contacts
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created
        # notification number must be 1
        #--------------------------------------------------------------
        print "- 1 x BAD get hard -------------------------------------"
        self.scheduler_loop(1, [[svc, 3, 'UNKNOWN']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        #self.show_and_clear_actions()
        print "TOTO2"
        self.show_actions()
        print "notif in progress", svc.notifications_in_progress
        for n in svc.notifications_in_progress.values():
            print "TOTO", n.__dict__
        # check_notification: yes (hard)
        print "---current_notification_number", svc.current_notification_number
        # The contact refuse our notification, so we are still at 0
        self.assertEqual(0, svc.current_notification_number)
        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 5 x BAD repeat -------------------------------------"
        self.scheduler_loop(1, [[svc, 3, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "cnn and cur", cnn, svc.current_notification_number

        cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 3, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "svc.current_notification_number, cnn", svc.current_notification_number, cnn

        #--------------------------------------------------------------
        # 2 cycles = 2 minutes = 2 new notifications
        #--------------------------------------------------------------
        cnn = svc.current_notification_number
        self.scheduler_loop(2, [[svc, 3, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "svc.current_notification_number, cnn", svc.current_notification_number, cnn

        #--------------------------------------------------------------
        # 2 cycles = 2 minutes = 2 new notifications (theoretically)
        # BUT: test_contact filters notifications
        # we do not raise current_notification_number if no mail was sent
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] DISABLE_CONTACT_SVC_NOTIFICATIONS;test_contact" % now
        self.sched.run_external_command(cmd)
        cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 3, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        self.assertEqual(cnn, svc.current_notification_number)
        #--------------------------------------------------------------
        # again a normal cycle
        # test_contact receives his mail
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] ENABLE_CONTACT_SVC_NOTIFICATIONS;test_contact" % now
        self.sched.run_external_command(cmd)
        #cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 3, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_and_clear_logs()
        self.show_actions()
        print "svc.current_notification_number, cnn", svc.current_notification_number, cnn
        #self.assertEqual(cnn + 1, svc.current_notification_number)
        #--------------------------------------------------------------
        # now recover. there must be no scheduled/inpoller notification
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']], do_sleep=True, sleep_time=0.1)

        # I do not want a notification of a recovery because
        # the user did not have the notif first!
        self.assert_no_log_match('notify-service')
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assertEqual(0, svc.current_notification_number)

    def test_svc_in_dt_and_crit_and_notif_interval_0(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.notification_interval = 0
        host.notification_options = 'c'
        svc.notification_options = 'c'

        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP'], [svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.assertEqual(0, svc.current_notification_number)
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created
        # notification number must be 1
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[host, 0, 'UP'], [svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_logs()
        self.show_actions()
        self.assert_log_match(1, 'SERVICE ALERT.*;CRITICAL;SOFT')
        self.assert_log_match(2, 'SERVICE EVENT HANDLER.*;CRITICAL;SOFT')
        self.assert_log_match(3, 'SERVICE ALERT.*;CRITICAL;HARD')
        self.assert_log_match(4, 'SERVICE EVENT HANDLER.*;CRITICAL;HARD')
        self.assert_log_match(5, 'SERVICE NOTIFICATION.*;CRITICAL;')
        self.assertEqual(1, svc.current_notification_number)
        self.clear_logs()
        self.clear_actions()
        #--------------------------------------------------------------
        # reset host/service state
        #--------------------------------------------------------------
        #self.scheduler_loop(1, [[host, 0, 'UP'], [svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        #self.assertEqual(0, svc.current_notification_number)
        duration = 2
        now = time.time()
        # fixed downtime valid for the next 5 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        #--------------------------------------------------------------
        # service reaches hard;2
        # no notificatio
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[host, 0, 'UP'], [svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE DOWNTIME ALERT.*;STARTED')
        self.assert_no_log_match('SERVICE NOTIFICATION.*;CRITICAL;')
        # To get out of the DT.
        self.scheduler_loop(2, [[host, 0, 'UP'], [svc, 2, 'BAD']], do_sleep=True, sleep_time=2)
        self.assert_no_log_match('SERVICE NOTIFICATION.*;CRITICAL;')
        self.assertEqual(1, svc.current_notification_number)
        self.show_and_clear_logs()
        self.show_and_clear_actions()

if __name__ == '__main__':
    unittest.main()
