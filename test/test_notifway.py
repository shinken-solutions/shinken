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

import time

from shinken_test import unittest, ShinkenTest


class TestConfig(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_notif_way.cfg')

    def test_contact_def(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the contact"
        now = time.time()
        contact = self.sched.contacts.find_by_name("test_contact")
        print "The contact", contact.__dict__

        print "All notification Way:"
        for nw in self.sched.notificationways:
            print "\t", nw.notificationway_name

        email_in_day = self.sched.notificationways.find_by_name('email_in_day')
        self.assertIn(email_in_day, contact.notificationways)
        email_s_cmd = email_in_day.service_notification_commands.pop()
        email_h_cmd = email_in_day.host_notification_commands.pop()

        sms_the_night = self.sched.notificationways.find_by_name('sms_the_night')
        self.assertIn(sms_the_night, contact.notificationways)
        sms_s_cmd = sms_the_night.service_notification_commands.pop()
        sms_h_cmd = sms_the_night.host_notification_commands.pop()

        # And check the criticity values
        self.assertEqual(0, email_in_day.min_business_impact)
        self.assertEqual(5, sms_the_night.min_business_impact)

        print "Contact notification way(s):"
        for nw in contact.notificationways:
            print "\t", nw.notificationway_name
            for c in nw.service_notification_commands:
                print "\t\t", c.get_name()

        contact_simple = self.sched.contacts.find_by_name("test_contact_simple")
        # It's the created notifway for this simple contact
        test_contact_simple_inner_notificationway = self.sched.notificationways.find_by_name("test_contact_simple_inner_notificationway")
        print "Simple contact"
        for nw in contact_simple.notificationways:
            print "\t", nw.notificationway_name
            for c in nw.service_notification_commands:
                print "\t\t", c.get_name()
        self.assertIn(test_contact_simple_inner_notificationway, contact_simple.notificationways)

        # we take as criticity a huge value from now
        huge_criticity = 5

        # Now all want* functions
        # First is ok with warning alerts
        self.assertEqual(True, email_in_day.want_service_notification(now, 'WARNING', 'PROBLEM', huge_criticity) )

        # But a SMS is now WAY for warning. When we sleep, we wake up for critical only guy!
        self.assertEqual(False, sms_the_night.want_service_notification(now, 'WARNING', 'PROBLEM', huge_criticity) )

        # Same with contacts now
        # First is ok for warning in the email_in_day nw
        self.assertEqual(True, contact.want_service_notification(now, 'WARNING', 'PROBLEM', huge_criticity) )
        # Simple is not ok for it
        self.assertEqual(False, contact_simple.want_service_notification(now, 'WARNING', 'PROBLEM', huge_criticity) )

        # Then for host notification
        # First is ok for warning in the email_in_day nw
        self.assertEqual(True, contact.want_host_notification(now, 'FLAPPING', 'PROBLEM', huge_criticity) )
        # Simple is not ok for it
        self.assertEqual(False, contact_simple.want_host_notification(now, 'FLAPPING', 'PROBLEM', huge_criticity) )

        # And now we check that we refuse SMS for a low level criticity
        # I do not want to be awaken by a dev server! When I sleep, I sleep!
        # (and my wife will kill me if I do...)

        # We take the EMAIL test because SMS got the night ony, so we take a very low value for criticity here
        self.assertEqual(False, email_in_day.want_service_notification(now, 'WARNING', 'PROBLEM', -1) )



if __name__ == '__main__':
    unittest.main()
