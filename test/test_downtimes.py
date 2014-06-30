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
# This file is used to test host- and service-downtimes.
#

from shinken_test import *

#time.time = original_time_time
#time.sleep = original_time_sleep

class TestDowntime(ShinkenTest):

    def test_schedule_fixed_svc_downtime(self):
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
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        time.sleep(20)
        self.scheduler_loop(1, [[svc, 0, 'OK']])

        print "downtime was scheduled. check its activity and the comment"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(svc.comments) == 1)
        self.assert_(svc.comments[0] in self.sched.comments.values())
        self.assert_(svc.downtimes[0].comment_id == svc.comments[0].id)

        self.scheduler_loop(1, [[svc, 0, 'OK']])

        print "good check was launched, downtime must be active"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.in_scheduled_downtime)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)

        self.scheduler_loop(1, [[svc, 2, 'BAD']])

        print "bad check was launched (SOFT;1), downtime must be active"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.in_scheduled_downtime)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)

        # now the state changes to hard
        self.scheduler_loop(1, [[svc, 2, 'BAD']])

        print "bad check was launched (HARD;2), downtime must be active"
        print svc.downtimes[0]
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.in_scheduled_downtime)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)

        scheduled_downtime_depth = svc.scheduled_downtime_depth
        cmd = "[%lu] DEL_SVC_DOWNTIME;%d" % (now, svc.downtimes[0].id)
        self.sched.run_external_command(cmd)
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(not svc.in_scheduled_downtime)
        self.assert_(svc.scheduled_downtime_depth < scheduled_downtime_depth)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(svc.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(svc.comments) == 1)

        # now a notification must be sent
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        # downtimes must have been deleted now
        self.assert_(len(self.sched.downtimes) == 0)
        self.assert_(len(svc.downtimes) == 0)
        self.assert_(len(self.sched.comments) == 0)
        self.assert_(len(svc.comments) == 0)

    def test_schedule_flexible_svc_downtime(self):
        self.print_header()
        #----------------------------------------------------------------
        # schedule a flexible downtime of 3 minutes for the host
        #----------------------------------------------------------------
        duration = 180
        now = time.time()
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;0;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        time.sleep(20)
        #----------------------------------------------------------------
        # check if a downtime object exists (scheduler and service)
        # check if the downtime is still inactive
        #----------------------------------------------------------------
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(svc.comments) == 1)
        self.assert_(svc.comments[0] in self.sched.comments.values())
        self.assert_(svc.downtimes[0].comment_id == svc.comments[0].id)
        #----------------------------------------------------------------
        # run the service and return an OK status
        # check if the downtime is still inactive
        #----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(not svc.in_scheduled_downtime)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        time.sleep(61)
        #----------------------------------------------------------------
        # run the service twice to get a soft critical status
        # check if the downtime is still inactive
        #----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(not svc.in_scheduled_downtime)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        time.sleep(61)
        #----------------------------------------------------------------
        # run the service again to get a hard critical status
        # check if the downtime is active now
        #----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.in_scheduled_downtime)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        #----------------------------------------------------------------
        # cancel the downtime
        # check if the downtime is inactive now and can be deleted
        #----------------------------------------------------------------
        scheduled_downtime_depth = svc.scheduled_downtime_depth
        cmd = "[%lu] DEL_SVC_DOWNTIME;%d" % (now, svc.downtimes[0].id)
        self.sched.run_external_command(cmd)
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(not svc.in_scheduled_downtime)
        self.assert_(svc.scheduled_downtime_depth < scheduled_downtime_depth)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(svc.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(svc.comments) == 1)
        time.sleep(61)
        #----------------------------------------------------------------
        # run the service again with a critical status
        # the downtime must have disappeared
        # a notification must be sent
        #----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(len(self.sched.downtimes) == 0)
        self.assert_(len(svc.downtimes) == 0)
        self.assert_(len(self.sched.comments) == 0)
        self.assert_(len(svc.comments) == 0)
        self.show_logs()
        self.show_actions()

    def test_schedule_fixed_host_downtime(self):
        self.print_header()
        # schedule a 2-minute downtime
        # downtime must be active
        # consume a good result, sleep for a minute
        # downtime must be active
        # consume a bad result
        # downtime must be active
        # no notification must be found in broks
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        print "test_schedule_fixed_host_downtime initialized"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 0)
        self.assert_(self.count_actions() == 0)
        #----------------------------------------------------------------
        # schedule a downtime of 10 minutes for the host
        #----------------------------------------------------------------
        duration = 600
        now = time.time()
        # fixed downtime valid for the next 10 minutes
        cmd = "[%lu] SCHEDULE_HOST_DOWNTIME;test_host_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)

        self.sched.run_external_command(cmd)
        self.sched.update_downtimes_and_comments()
        print "Launch scheduler loop"
        self.scheduler_loop(1, [], do_sleep=False)  # push the downtime notification
        self.show_actions()
        print "Launch worker loop"
        #self.worker_loop()
        self.show_actions()
        print "After both launchs"
        time.sleep(20)
        #----------------------------------------------------------------
        # check if a downtime object exists (scheduler and host)
        #----------------------------------------------------------------
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(host.downtimes) == 1)
        self.assert_(host.downtimes[0] in self.sched.downtimes.values())
        self.assert_(host.downtimes[0].fixed)
        self.assert_(host.downtimes[0].is_in_effect)
        self.assert_(not host.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(host.comments) == 1)
        self.assert_(host.comments[0] in self.sched.comments.values())
        self.assert_(host.downtimes[0].comment_id == host.comments[0].id)
        self.show_logs()
        self.show_actions()
        print "*****************************************************************************************************************************************************************Log matching:", self.get_log_match("STARTED*")
        self.show_actions()
        self.assert_(self.count_logs() == 2)    # start downt, notif downt
        print self.count_actions() # notif" down is removed, so only donwtime
        self.assert_(self.count_actions() == 1)
        self.scheduler_loop(1, [], do_sleep=False)
        self.show_logs()
        self.show_actions()
        
        self.assert_(self.count_logs() == 2)    # start downt, notif downt
        self.clear_logs()
        self.clear_actions()
        #----------------------------------------------------------------
        # send the host to a hard DOWN state
        # check log messages, (no) notifications and eventhandlers
        #----------------------------------------------------------------
        self.scheduler_loop(1, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 2)    # soft1, evt1
        self.assert_(self.count_actions() == 1)  # evt1
        self.clear_logs()
        #--
        self.scheduler_loop(1, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 2)    # soft2, evt2
        self.assert_(self.count_actions() == 1)  # evt2
        self.clear_logs()
        #--
        self.scheduler_loop(1, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 2)    # hard3, evt3
        self.assert_(self.count_actions() == 2)  # evt3, notif"
        self.clear_logs()
        #--
        # we have a notification, but this is blocked. it will stay in
        # the actions queue because we have a notification_interval.
        # it's called notif" because it is a master notification
        print "DBG: host", host.state, host.state_type
        self.scheduler_loop(1, [[host, 2, 'DOWN']], do_sleep=True)
        print "DBG2: host", host.state, host.state_type
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 0)     #
        self.assert_(self.count_actions() == 1)  # notif"
        self.clear_logs()
        #----------------------------------------------------------------
        # the host comes UP again
        # check log messages, (no) notifications and eventhandlers
        # a (recovery) notification was created, but has been blocked.
        # should be a zombie, but was deteleted
        #----------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']], do_sleep=True)
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 2)    # hard3ok, evtok
        self.assert_(self.count_actions() == 1)  # evtok, notif"
        self.clear_logs()
        self.clear_actions()

    def test_schedule_fixed_host_downtime_with_service(self):
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        host.notification_interval = 0
        svc.notification_interval = 0
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 0)
        self.assert_(self.count_actions() == 0)
        #----------------------------------------------------------------
        # schedule a downtime of 10 minutes for the host
        #----------------------------------------------------------------
        duration = 600
        now = time.time()
        cmd = "[%lu] SCHEDULE_HOST_DOWNTIME;test_host_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        self.sched.update_downtimes_and_comments()
        self.scheduler_loop(1, [], do_sleep=False)  # push the downtime notification
        #self.worker_loop() # push the downtime notification
        time.sleep(10)
        #----------------------------------------------------------------
        # check if a downtime object exists (scheduler and host)
        # check the start downtime notification
        #----------------------------------------------------------------
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(host.downtimes) == 1)
        self.assert_(host.in_scheduled_downtime)
        self.assert_(host.downtimes[0] in self.sched.downtimes.values())
        self.assert_(host.downtimes[0].fixed)
        self.assert_(host.downtimes[0].is_in_effect)
        self.assert_(not host.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(host.comments) == 1)
        self.assert_(host.comments[0] in self.sched.comments.values())
        self.assert_(host.downtimes[0].comment_id == host.comments[0].id)
        self.scheduler_loop(4, [[host, 2, 'DOWN']], do_sleep=True)
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 8)    # start downt, notif downt, soft1, evt1, soft 2, evt2, hard 3, evt3
        self.clear_logs()
        self.clear_actions()
        #----------------------------------------------------------------
        # now the service becomes critical
        # check that the host has a downtime, _not_ the service
        # check logs, (no) notifications and eventhandlers
        #----------------------------------------------------------------
        print "now the service goes critical"
        self.scheduler_loop(4, [[svc, 2, 'CRITICAL']], do_sleep=True)
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 0)
        self.assert_(not svc.in_scheduled_downtime)
        self.assert_(svc.host.in_scheduled_downtime)
        self.show_logs()
        self.show_actions()
        # soft 1, evt1, hard 2, evt2
        self.assert_(self.count_logs() == 4)
        self.clear_logs()
        self.clear_actions()
        #----------------------------------------------------------------
        # the host comes UP again
        # check log messages, (no) notifications and eventhandlers
        #----------------------------------------------------------------
        print "now the host comes up"
        self.scheduler_loop(2, [[host, 0, 'UP']], do_sleep=True)
        self.show_logs()
        self.show_actions()
        # hard 3, eventhandler
        self.assert_(self.count_logs() == 2)    # up, evt
        self.clear_logs()
        self.clear_actions()
        #----------------------------------------------------------------
        # the service becomes OK again
        # check log messages, (no) notifications and eventhandlers
        # check if the stop downtime notification is the only one
        #----------------------------------------------------------------
        self.scheduler_loop(2, [[host, 0, 'UP']], do_sleep=True)
        self.assert_(len(self.sched.downtimes) == 0)
        self.assert_(len(host.downtimes) == 0)
        self.assert_(not host.in_scheduled_downtime)
        self.show_logs()
        self.show_actions()
        self.assert_(self.log_match(1, 'HOST DOWNTIME ALERT.*STOPPED'))
        self.clear_logs()
        self.clear_actions()
        # todo
        # checks return 1=warn. this means normally up
        # set use_aggressive_host_checking which treats warn as down

        # send host into downtime
        # run service checks with result critical
        # host exits downtime
        # does the service send a notification like when it exts a svc dt?
        # check for notifications

        # host is down and in downtime. what about service eventhandlers?

    def test_notification_after_cancel_flexible_svc_downtime(self):
        # schedule flexible downtime
        # good check
        # bad check -> SOFT;1
        #  eventhandler SOFT;1
        # bad check -> HARD;2
        #  downtime alert
        #  eventhandler HARD;2
        # cancel downtime
        # bad check -> HARD;2
        #  notification critical
        #
        pass

if __name__ == '__main__':
    unittest.main()
