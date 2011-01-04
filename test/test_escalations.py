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
# This file is used to test host- and service-downtimes.
#


#It's ugly I know....
from shinken_test import *


class TestEscalations(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/nagios_escalations.cfg')


    def test_simple_escalation(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")

        #To make tests quicker we make notifications send very quickly
        svc.notification_interval = 0.001
        
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)

        self.assert_(svc.current_notification_number == 0)
        
        tolevel2 = self.sched.conf.escalations.find_by_name('ToLevel2')
        self.assert_(tolevel2 != None)
        self.assert_(tolevel2 in svc.escalations)
        tolevel3 = self.sched.conf.escalations.find_by_name('ToLevel3')
        self.assert_(tolevel3 != None)
        self.assert_(tolevel3 in svc.escalations)


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
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level1.*;CRITICAL;'))
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
        self.assert_(svc.current_notification_number == 1)
        print "OK, level1 is notified, notif nb = 1"
        
        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 1 x BAD repeat -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        
        # Now we raise the notif number of 2, so we can escalade
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;'))
        self.show_and_clear_logs()
        self.show_actions()
        print "cnn and cur", cnn, svc.current_notification_number
        self.assert_(svc.current_notification_number > cnn)
        cnn = svc.current_notification_number

        # One more bad, we go 3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;'))
        self.show_and_clear_logs()

        # We go 4, still level2
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;'))
        self.show_and_clear_logs()

        # We go 5! we escalade to level3

        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;'))
        self.show_and_clear_logs()

        # Now we send 10 more notif, we must be still level5
        for i in range(10):
            self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
            self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;'))
            self.show_and_clear_logs()

        # Now we recover, it will be fun because all of level{1,2,3} must be send a
        # notif
        self.scheduler_loop(2, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level1.*;OK;'))
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;OK;'))
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;OK;'))
        self.show_and_clear_logs()




    def test_time_based_escalation(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0_time")

        #To make tests quicker we make notifications send very quickly
        svc.notification_interval = 0.001
        
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)

        self.assert_(svc.current_notification_number == 0)
        
        tolevel2_time = self.sched.conf.escalations.find_by_name('ToLevel2-time')
        self.assert_(tolevel2_time != None)
        self.assert_(tolevel2_time in svc.escalations)
        tolevel3_time = self.sched.conf.escalations.find_by_name('ToLevel3-time')
        self.assert_(tolevel3_time != None)
        self.assert_(tolevel3_time in svc.escalations)


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
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level1.*;CRITICAL;'))
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
        self.assert_(svc.current_notification_number == 1)
        print "OK, level1 is notified, notif nb = 1"
        
        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 1 x BAD repeat -------------------------------------"
        
        # For the test, we hack the notif value
        print "DBG:", svc.notifications_in_progress
        for n in svc.notifications_in_progress.values():
            print "COCO", n.__dict__
            # HOP, we say : it's already 3600 second since the last notif,
            svc.notification_interval = 3600
            # and we say that there is still 1hour since the notification creation
            n.creation_time = n.creation_time - 3600

        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.001)
        
        # Now we raise the notif number of 2, so we can escalade

        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;'))
        self.show_and_clear_logs()

        self.show_actions()
        print "cnn and cur", cnn, svc.current_notification_number
        self.assert_(svc.current_notification_number > cnn)
        cnn = svc.current_notification_number

        #svc.notification_interval = 0.001
        for n in svc.notifications_in_progress.values():
            print "COCO", n.__dict__
            # HOP, we say : it's already 3600 second since the last notif,
            n.t_to_go = time.time()
            


        # One more bad, we say : he, it's 7200 sc of notif, so must be still level2
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;'))
        self.show_and_clear_logs()

        #svc.notification_interval = 0.001
        for n in svc.notifications_in_progress.values():
            print "COCO", n.__dict__
            # HOP, we say : it's already 3600 second since the last notif,
            n.t_to_go = time.time()
            n.creation_time = n.creation_time - 3600
            

        # One more, we bypass 7200, so now it's level3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;'))
        self.show_and_clear_logs()

        #One more time...
        #svc.notification_interval = 0.001


        # Now we send 10 more notif, we must be still level5
        for i in range(10):
            for n in svc.notifications_in_progress.values():
                print "COCO", n.__dict__
                # HOP, we say : it's already 3600 second since the last notif,
                n.t_to_go = time.time()

            self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
            self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;'))
            self.show_and_clear_logs()

        # Now we recover, it will be fun because all of level{1,2,3} must be send a
        # notif
        self.scheduler_loop(2, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level1.*;OK;'))
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;OK;'))
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;OK;'))
        self.show_and_clear_logs()





    def test_time_based_escalation_with_shorting_interval(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0_time")

        #To make tests quicker we make notifications send very quickly
        #svc.notification_interval = 0.001
        svc.notification_interval = 1400
        
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True, sleep_time=0.1)
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)

        self.assert_(svc.current_notification_number == 0)
        
        tolevel2_time = self.sched.conf.escalations.find_by_name('ToLevel2-time')
        self.assert_(tolevel2_time != None)
        self.assert_(tolevel2_time in svc.escalations)
        tolevel3_time = self.sched.conf.escalations.find_by_name('ToLevel3-time')
        self.assert_(tolevel3_time != None)
        self.assert_(tolevel3_time in svc.escalations)


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
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level1.*;CRITICAL;'))
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
        self.assert_(svc.current_notification_number == 1)
        print "OK, level1 is notified, notif nb = 1"
        
        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 1 x BAD repeat -------------------------------------"
        
        # For the test, we hack the notif value
        print "DBG:", svc.notifications_in_progress
        for n in svc.notifications_in_progress.values():
            print "COCO", n.__dict__, time.asctime(time.localtime(n.t_to_go)), time.asctime(time.localtime(time.time()))
            # HOP, we say : it's already 3600 second since the last notif,
#            svc.notification_interval = 3600

        print "*************Next", svc.notification_interval * svc.__class__.interval_length
        for n in svc.notifications_in_progress.values():

            print "NOW:", time.asctime(time.localtime(time.time()))
            print tolevel2_time.__dict__
            next = svc.get_next_notification_time(n)
            print next - now
            # Check if we find the next notification for the next hour,
            # and not for the next day like we ask before
            self.assert_(abs(next - now - 3600) < 10) 

        for n in svc.notifications_in_progress.values():
             print "TOTO", n
             n.t_to_go = time.time()
             n.creation_time -= 3600
        
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.001)

        # Now we raise the notif number of 2, so we can escalade

        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;CRITICAL;'))
        self.show_and_clear_logs()

        print "OK " * 10
        print "Level 2 got warn, now we search for level3"

        self.show_actions()
        print "cnn and cur", cnn, svc.current_notification_number
        self.assert_(svc.current_notification_number > cnn)
        cnn = svc.current_notification_number

        #svc.notification_interval = 0.001
        for n in svc.notifications_in_progress.values():
            print "COCO", n.__dict__
            # HOP, we say : it's already 3600 second since the last notif,
            n.t_to_go = time.time()
            n.creation_time -= 3600


        # One more bad, we say : he, it's 7200 sc of notif, so must be still level3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;'))
        self.show_and_clear_logs()

        #svc.notification_interval = 0.001
        for n in svc.notifications_in_progress.values():
            print "COCO", n.__dict__
            # HOP, we say : it's already 3600 second since the last notif,
            n.t_to_go = time.time()

        # One more, we bypass 7200, so now it's still level3
        self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;'))
        self.show_and_clear_logs()

        #One more time...
        #svc.notification_interval = 0.001


        # Now we send 10 more notif, we must be still level5
        for i in range(10):
            for n in svc.notifications_in_progress.values():
                print "COCO", n.__dict__
                # HOP, we say : it's already 3600 second since the last notif,
                n.t_to_go = time.time()

            self.scheduler_loop(1, [[svc, 2, 'BAD']], do_sleep=True, sleep_time=0.1)
            self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;CRITICAL;'))
            self.show_and_clear_logs()

        # Now we recover, it will be fun because all of level{1,2,3} must be send a
        # notif
        self.scheduler_loop(2, [[svc, 0, 'OK']], do_sleep=True, sleep_time=0.1)
        self.show_actions()
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level1.*;OK;'))
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level2.*;OK;'))
        self.assert_(self.any_log_match('SERVICE NOTIFICATION: level3.*;OK;'))
        self.show_and_clear_logs()



if __name__ == '__main__':
    unittest.main()
