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

from shinken_test import *
from shinken.objects.serviceescalation import Serviceescalation

class TestEscalations(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_escalations.cfg')
        time_hacker.set_real_time()

    def test_wildcard_in_service_descrption(self):
        self.print_header()
        sid = int(Serviceescalation.id) - 1
        generated = self.sched.conf.escalations.find_by_name('Generated-Serviceescalation-%d' % sid)
        for svc in self.sched.services.find_srvs_by_hostname("test_host_0"):
            self.assertIn(generated, svc.escalations)

    def test_simple_escalation(self):
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

        tolevel2 = self.sched.conf.escalations.find_by_name('ToLevel2')
        self.assertIsNot(tolevel2, None)
        self.assertIn(tolevel2, svc.escalations)
        tolevel3 = self.sched.conf.escalations.find_by_name('ToLevel3')
        self.assertIsNot(tolevel3, None)
        self.assertIn(tolevel3, svc.escalations)


        for es in svc.escalations:
            print es.__dict__

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

        # We check if we really notify the level1
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;CRITICAL;')
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
        print "OK, level1 is notified, notif nb = 1"

        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 1 x BAD repeat -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assertIn(True, [n.escalated for n in self.sched.actions.values()])

        # Now we raise the notif number of 2, so we can escalade
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()
        print "cnn and cur", cnn, svc.current_notification_number
        self.assertGreater(svc.current_notification_number, cnn)
        cnn = svc.current_notification_number

        # One more bad, we go 3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assertIn(True, [n.escalated for n in self.sched.actions.values()])
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()

        # We go 4, still level2
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assertIn(True, [n.escalated for n in self.sched.actions.values()])
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()
        # We go 5! we escalade to level3

        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assertIn(True, [n.escalated for n in self.sched.actions.values()])
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
        self.show_and_clear_logs()

        # Now we send 10 more notif, we must be still level5
        for i in range(10):
            self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
            self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
            self.show_and_clear_logs()

        # Now we recover, it will be fun because all of level{1,2,3} must be send a
        # notif
        self.scheduler_loop(2, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;OK;')
        self.show_and_clear_logs()

    def test_time_based_escalation(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0_time")

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

        # We check if we correclty linked our escalations
        tolevel2_time = self.sched.conf.escalations.find_by_name('ToLevel2-time')
        self.assertIsNot(tolevel2_time, None)
        self.assertIn(tolevel2_time, svc.escalations)
        tolevel3_time = self.sched.conf.escalations.find_by_name('ToLevel3-time')
        self.assertIsNot(tolevel3_time, None)
        self.assertIn(tolevel3_time, svc.escalations)

        # Go for the running part!

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

        # We check if we really notify the level1
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()

        # check_notification: yes (hard)
        print "---current_notification_number", svc.current_notification_number
        # notification_number is already sent. the next one has been scheduled
        # and is waiting for notification_interval to pass. so the current
        # number is 2
        self.assertEqual(1, svc.current_notification_number)
        print "OK, level1 is notified, notif nb = 1"

        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 1 x BAD repeat -------------------------------------"

        # For the test, we hack the notif value because we do not wan to wait 1 hour!
        for n in svc.notifications_in_progress.values():
            # HOP, we say: it's already 3600 second since the last notif,
            svc.notification_interval = 3600
            # and we say that there is still 1hour since the notification creation
            # so it will say the notification time is huge, and so it will escalade
            n.creation_time = n.creation_time - 3600

        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.001)

        # Now we raise a notification time of 1hour, we escalade to level2
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()

        print "cnn and cur", cnn, svc.current_notification_number
        # We check that we really raise the notif number too
        self.assertGreater(svc.current_notification_number, cnn)
        cnn = svc.current_notification_number

        for n in svc.notifications_in_progress.values():
            # HOP, we say: it's already 3600 second since the last notif
            n.t_to_go = time.time()

        # One more bad, we say: he, it's still near 1 hour, so still level2
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()

        # Now we go for level3, so again we say: he, in fact we start one hour earlyer,
        # so the total notification duration is near 2 hour, so we will raise level3
        for n in svc.notifications_in_progress.values():
            # HOP, we say: it's already 3600 second since the last notif,
            n.t_to_go = time.time()
            n.creation_time = n.creation_time - 3600

        # One more, we bypass 7200, so now it's level3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
        self.show_and_clear_logs()


        # Now we send 10 more notif, we must be still level5
        for i in range(10):
            for n in svc.notifications_in_progress.values():
                # HOP, we say: it's already 3600 second since the last notif,
                n.t_to_go = time.time()

            self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
            self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
            self.show_and_clear_logs()

        # Now we recover, it will be fun because all of level{1,2,3} must be send a
        # recovery notif
        self.scheduler_loop(2, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;OK;')
        self.show_and_clear_logs()

    # Here we search to know if a escalation really short the notification
    # interval if the escalation if BEFORE the next notification. For example
    # let say we notify one a day, if the escalation if at 4hour, we need
    # to notify at t=0, and get the next notification at 4h, and not 1day.
    def test_time_based_escalation_with_shorting_interval(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0_time")

        # To make tests quicker we make notifications send very quickly
        # 1 day notification interval
        svc.notification_interval = 1400

        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)

        self.assertEqual(0, svc.current_notification_number)

        # We check that we really linked our escalations :)
        tolevel2_time = self.sched.conf.escalations.find_by_name('ToLevel2-time')
        self.assertIsNot(tolevel2_time, None)
        self.assertIn(tolevel2_time, svc.escalations)
        tolevel3_time = self.sched.conf.escalations.find_by_name('ToLevel3-time')
        self.assertIsNot(tolevel3_time, None)
        self.assertIn(tolevel3_time, svc.escalations)

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

        print "  ** LEVEL1 ** " * 20
        # We check if we really notify the level1
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()

        # check_notification: yes (hard)
        print "---current_notification_number", svc.current_notification_number
        # notification_number is already sent. the next one has been scheduled
        # and is waiting for notification_interval to pass. so the current
        # number is 2
        self.assertEqual(1, svc.current_notification_number)
        print "OK, level1 is notified, notif nb = 1"

        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 1 x BAD repeat -------------------------------------"

        # Now we go for the level2 escalation, so we will need to say: he, it's 1 hour since the begining:p
        print "*************Next", svc.notification_interval * svc.__class__.interval_length

        # first, we check if the next notification will really be near 1 hour because the escalation
        # to level2 is asking for it. If it don't, the standard was 1 day!
        for n in svc.notifications_in_progress.values():
            next = svc.get_next_notification_time(n)
            print abs(next - now)
            # Check if we find the next notification for the next hour,
            # and not for the next day like we ask before
            self.assertLess(abs(next - now - 3600), 10)

        # And we hack the notification so we can raise really the level2 escalation
        for n in svc.notifications_in_progress.values():
            n.t_to_go = time.time()
            n.creation_time -= 3600

        print "  ** LEVEL2 ** " * 20

        # We go in trouble too
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.001)

        # Now we raise the time since the begining at 1 hour, so we can escalade
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()

        print "Level 2 got warn, now we search for level3"
        print "cnn and cur", cnn, svc.current_notification_number
        self.assertGreater(svc.current_notification_number, cnn)
        cnn = svc.current_notification_number

        # Now the same thing, but for level3, so one more hour
        for n in svc.notifications_in_progress.values():
            # HOP, we say: it's already 3600 second since the last notif,
            n.t_to_go = time.time()
            n.creation_time -= 3600

        # One more bad, we say: he, it's 7200 sc of notif, so must be still level3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
        self.show_and_clear_logs()

        for n in svc.notifications_in_progress.values():
            # we say that the next notif will be right now
            # so we can raise a notif now
            n.t_to_go = time.time()

        # One more, we bypass 7200, so now it's still level3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
        self.show_and_clear_logs()


        # Now we send 10 more notif, we must be still level3
        for i in range(10):
            for n in svc.notifications_in_progress.values():
                # HOP, we say: it's already 3600 second since the last notif,
                n.t_to_go = time.time()

            self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
            self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
            self.show_and_clear_logs()

        # Ok now we get the normal stuff, we do NOT want to raise so soon a
        # notification.
        self.scheduler_loop(2, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        print svc.notifications_in_progress
        # Should be far away
        for n in svc.notifications_in_progress.values():
            print n, n.t_to_go, time.time(), n.t_to_go - time.time()
            # Should be "near" one day now, so 84000s
            self.assertLess(8300 < abs(n.t_to_go - time.time()), 85000)
        # And so no notification
        self.assert_no_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')

        # Now we recover, it will be fun because all of level{1,2,3} must be send a
        # recovery notif
        self.scheduler_loop(2, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;OK;')
        self.show_and_clear_logs()

    def test_time_based_escalation_with_short_notif_interval(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0_time_long_notif_interval")
        # For this specific test, notif interval will be something like 10s
        #svc.notification_interval = 0.1

        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)

        self.assertEqual(0, svc.current_notification_number)

        # We hack the interval_length for short time, like 10s
        svc.__class__.interval_length = 5

        # We check if we correclty linked our escalations
        tolevel2_time = self.sched.conf.escalations.find_by_name('ToLevel2-shortinterval')
        self.assertIsNot(tolevel2_time, None)
        self.assertIn(tolevel2_time, svc.escalations)
        #tolevel3_time = self.sched.conf.escalations.find_by_name('ToLevel3-time')
        #self.assertIsNot(tolevel3_time, None)
        #self.assertIn(tolevel3_time, svc.escalations)

        # Go for the running part!

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

        # We check if we really notify the level1
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()

        # check_notification: yes (hard)
        print "---current_notification_number", svc.current_notification_number
        # notification_number is already sent. the next one has been scheduled
        # and is waiting for notification_interval to pass. so the current
        # number is 2
        self.assertEqual(1, svc.current_notification_number)
        print "OK, level1 is notified, notif nb = 1"

        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 1 x BAD repeat -------------------------------------"

        # For the test, we hack the notif value because we do not wan to wait 1 hour!
        #for n in svc.notifications_in_progress.values():
            # HOP, we say: it's already 3600 second since the last notif,
        #    svc.notification_interval = 3600
            # and we say that there is still 1hour since the notification creation
            # so it will say the notification time is huge, and so it will escalade
        #    n.creation_time = n.creation_time - 3600

        # Sleep 1min and look how the notification is going, only 6s because we will go in
        # escalation in 5s (5s = interval_length, 1 for escalation time)
        print "---" * 200
        print "We wait a bit, but not enough to go in escalation level2"
        time.sleep(2)

        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.001)

        # Now we raise a notification time of 1hour, we escalade to level2
        self.assert_no_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()

        print "---" * 200
        print "OK NOW we will have an escalation!"
        time.sleep(5)

        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.001)

        # Now we raise a notification time of 1hour, we escalade to level2
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()
        self.show_actions()

        print "cnn and cur", cnn, svc.current_notification_number
        # We check that we really raise the notif number too
        self.assertGreater(svc.current_notification_number, cnn)
        cnn = svc.current_notification_number
        
        # Ok we should have one notification
        next_notifications = svc.notifications_in_progress.values()
        print "LEN", len(next_notifications)
        for n in next_notifications:
            print n
        self.assertEqual(1, len(next_notifications))
        n = next_notifications.pop()
        print "Current NOTIFICATION", n.__dict__, n.t_to_go, time.time(), n.t_to_go - time.time(), n.already_start_escalations
        # Should be in the escalation ToLevel2-shortinterval
        self.assertIn('ToLevel2-shortinterval', n.already_start_escalations)

        # Ok we want to be sure we are using the current escalation interval, the 1 interval = 5s
        # So here we should have a new notification for level2
        print "*--*--" * 20
        print "Ok now another notification during the escalation 2"
        time.sleep(10)

        # One more bad, we say: he, it's still near 1 hour, so still level2
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.show_and_clear_logs()

        # Ok now go in the Level3 thing
        print "*--*--" * 20
        print "Ok now goes in level3 too"
        time.sleep(10)

        # One more, we bypass 7200, so now it's level3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
        self.show_and_clear_logs()

        # Ok we should have one notification
        next_notifications = svc.notifications_in_progress.values()
        self.assertEqual(1, len(next_notifications))
        n = next_notifications.pop()
        print "Current NOTIFICATION", n.__dict__, n.t_to_go, time.time(), n.t_to_go - time.time(), n.already_start_escalations
        # Should be in the escalation ToLevel2-shortinterval
        self.assertIn('ToLevel2-shortinterval', n.already_start_escalations)
        self.assertIn('ToLevel3-shortinterval', n.already_start_escalations)

        # Make a loop for pass the next notification
        time.sleep(5)
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
        self.show_and_clear_logs()

        print "Current NOTIFICATION", n.__dict__, n.t_to_go, time.time(), n.t_to_go - time.time(), n.already_start_escalations

        # Now way a little bit, and with such low value, the escalation3 value must be ok for this test to pass
        time.sleep(5)

        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;')
        self.show_and_clear_logs()

        # Now we recover, it will be fun because all of level{1,2,3} must be send a
        # recovery notif
        self.scheduler_loop(2, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        self.assert_any_log_match('SERVICE NOTIFICATION: level1.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level2.*;OK;')
        self.assert_any_log_match('SERVICE NOTIFICATION: level3.*;OK;')
        self.show_and_clear_logs()




if __name__ == '__main__':
    unittest.main()
