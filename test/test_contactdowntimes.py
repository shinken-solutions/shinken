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


class TestContactDowntime(ShinkenTest):

    def test_contact_downtime(self):
        self.print_header()
        # schedule a 2-minute downtime
        # downtime must be active
        # consume a good result, sleep for a minute
        # downtime must be active
        # consume a bad result
        # downtime must be active
        # no notification must be found in broks
        duration = 600
        now = time.time()
        # downtime valid for the next 2 minutes
        test_contact = self.sched.contacts.find_by_name('test_contact')
        cmd = "[%lu] SCHEDULE_CONTACT_DOWNTIME;test_contact;%d;%d;lausser;blablub" % (now, now, now + duration)
        self.sched.run_external_command(cmd)

        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # Change the notif interval, so we can notify as soon as we want
        svc.notification_interval = 0.001

        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router

        #time.sleep(20)
        # We loop, the downtime wil be check and activate
        self.scheduler_loop(1, [[svc, 0, 'OK'], [host, 0, 'UP']])

        self.assert_any_log_match('CONTACT DOWNTIME ALERT.*;STARTED')
        self.show_and_clear_logs()

        print "downtime was scheduled. check its activity and the comment\n"*5
        self.assertEqual(1, len(self.sched.contact_downtimes))
        self.assertEqual(1, len(test_contact.downtimes))
        self.assertIn(test_contact.downtimes[0], self.sched.contact_downtimes.values())

        self.assertTrue(test_contact.downtimes[0].is_in_effect)
        self.assertFalse(test_contact.downtimes[0].can_be_deleted)

        # Ok, we define the downtime like we should, now look at if it does the job: do not
        # raise notif during a downtime for this contact
        self.scheduler_loop(3, [[svc, 2, 'CRITICAL']])

        # We should NOT see any service notification
        self.assert_no_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

        # Now we short the downtime a lot so it will be stop at now + 1 sec.
        test_contact.downtimes[0].end_time = time.time() + 1

        time.sleep(2)

        # We invalidate it with a scheduler loop
        self.scheduler_loop(1, [])

        # So we should be out now, with a log
        self.assert_any_log_match('CONTACT DOWNTIME ALERT.*;STOPPED')
        self.show_and_clear_logs()

        print "\n\nDowntime was ended. Check it is really stopped"
        self.assertEqual(0, len(self.sched.contact_downtimes))
        self.assertEqual(0, len(test_contact.downtimes))

        for n in svc.notifications_in_progress.values():
            print "NOTIF", n, n.t_to_go, time.time()

        # Now we want this contact to be really notify!
        # Ok, we define the downtime like we should, now look at if it does the job: do not
        # raise notif during a downtime for this contact
        time.sleep(1)
        self.scheduler_loop(3, [[svc, 2, 'CRITICAL']])
        self.assert_any_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

        for n in svc.notifications_in_progress.values():
            print "NOTIF", n, n.t_to_go, time.time(), time.time() - n.t_to_go


    def test_contact_downtime_and_cancel(self):
        self.print_header()
        # schedule a 2-minute downtime
        # downtime must be active
        # consume a good result, sleep for a minute
        # downtime must be active
        # consume a bad result
        # downtime must be active
        # no notification must be found in broks
        duration = 600
        now = time.time()
        # downtime valid for the next 2 minutes
        test_contact = self.sched.contacts.find_by_name('test_contact')
        cmd = "[%lu] SCHEDULE_CONTACT_DOWNTIME;test_contact;%d;%d;lausser;blablub" % (now, now, now + duration)
        self.sched.run_external_command(cmd)

        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # Change the notif interval, so we can notify as soon as we want
        svc.notification_interval = 0.001

        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router

        #time.sleep(20)
        # We loop, the downtime wil be check and activate
        self.scheduler_loop(1, [[svc, 0, 'OK'], [host, 0, 'UP']])

        self.assert_any_log_match('CONTACT DOWNTIME ALERT.*;STARTED')
        self.show_and_clear_logs()

        print "downtime was scheduled. check its activity and the comment"
        self.assertEqual(1, len(self.sched.contact_downtimes))
        self.assertEqual(1, len(test_contact.downtimes))
        self.assertIn(test_contact.downtimes[0], self.sched.contact_downtimes.values())

        self.assertTrue(test_contact.downtimes[0].is_in_effect)
        self.assertFalse(test_contact.downtimes[0].can_be_deleted)

        time.sleep(1)
        # Ok, we define the downtime like we should, now look at if it does the job: do not
        # raise notif during a downtime for this contact
        self.scheduler_loop(3, [[svc, 2, 'CRITICAL']])

        # We should NOT see any service notification
        self.assert_no_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()

        downtime_id = test_contact.downtimes[0].id
        # OK, Now we cancel this downtime, we do not need it anymore
        cmd = "[%lu] DEL_CONTACT_DOWNTIME;%d" % (now, downtime_id)
        self.sched.run_external_command(cmd)

        # We check if the downtime is tag as to remove
        self.assertTrue(test_contact.downtimes[0].can_be_deleted)

        # We really delete it
        self.scheduler_loop(1, [])

        # So we should be out now, with a log
        self.assert_any_log_match('CONTACT DOWNTIME ALERT.*;CANCELLED')
        self.show_and_clear_logs()

        print "Downtime was cancelled"
        self.assertEqual(0, len(self.sched.contact_downtimes))
        self.assertEqual(0, len(test_contact.downtimes))

        time.sleep(1)
        # Now we want this contact to be really notify!
        # Ok, we define the downtime like we should, now look at if it does the job: do not
        # raise notif during a downtime for this contact
        self.scheduler_loop(3, [[svc, 2, 'CRITICAL']])
        self.assert_any_log_match('SERVICE NOTIFICATION.*;CRITICAL')
        self.show_and_clear_logs()



if __name__ == '__main__':
    unittest.main()
