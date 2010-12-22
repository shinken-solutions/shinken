#!/usr/bin/env python2.6
#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

#It's ugly I know....
from shinken_test import *


class TestConfig(ShinkenTest):
    #setUp is in shinken_test
    def setUp(self):
        self.setup_with_file('etc/nagios_notif_way.cfg')


    #Change ME :)
    def test_contact_def(self):
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the contact"
        now = time.time()
        contact = self.sched.contacts.find_by_name("test_contact")
        print "The contact", contact.__dict__

        print "All notification Way :"
        for nw in self.sched.notificationways:
            print "\t", nw.notificationway_name

        email_in_day = self.sched.notificationways.find_by_name('email_in_day')
        self.assert_(email_in_day in contact.notificationways)

        sms_the_night = self.sched.notificationways.find_by_name('sms_the_night')
        self.assert_(sms_the_night in contact.notificationways)
        
        # And check the criticity values
        self.assert_(email_in_day.min_criticity == 0)
        self.assert_(sms_the_night.min_criticity == 5)
        

        print "Contact notification way(s) :"
        for nw in contact.notificationways:
            print "\t", nw.notificationway_name

        contact_simple = self.sched.contacts.find_by_name("test_contact_simple")
        #It's the created notifway for this simple contact
        test_contact_simple_inner_notificationway = self.sched.notificationways.find_by_name("test_contact_simple_inner_notificationway")
        print "Simple contact"
        for nw in contact_simple.notificationways:
            print "\t", nw.notificationway_name
        self.assert_(test_contact_simple_inner_notificationway in contact_simple.notificationways)

        #Now all want* functions
        #First is ok with warning alerts
        self.assert_(email_in_day.want_service_notification(now, 'WARNING', 'PROBLEM') == True)

        #But a SMS is now WAY for warning. When we sleep, we wake up for critical only guy!
        self.assert_(sms_the_night.want_service_notification(now, 'WARNING', 'PROBLEM') == False)

        #Same with contacts now
        #First is ok for warning in the email_in_day nw
        self.assert_(contact.want_service_notification(now, 'WARNING', 'PROBLEM') == True)
        #Simple is not ok for it
        self.assert_(contact_simple.want_service_notification(now, 'WARNING', 'PROBLEM') == False)

        #Then for host notification
        #First is ok for warning in the email_in_day nw
        self.assert_(contact.want_host_notification(now, 'FLAPPING', 'PROBLEM') == True)
        #Simple is not ok for it
        self.assert_(contact_simple.want_host_notification(now, 'FLAPPING', 'PROBLEM') == False)



if __name__ == '__main__':
    unittest.main()

