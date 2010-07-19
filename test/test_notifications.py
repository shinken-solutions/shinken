#!/usr/bin/env python2.6

#
# This file is used to test host- and service-downtimes.
#

import sys
import time
import os
import string
import re
import random
import unittest
sys.path.append("../src")
from config import Config
from dispatcher import Dispatcher
from log import Log
from scheduler import Scheduler
from macroresolver import MacroResolver
from external_command import ExternalCommand
from check import Check

class TestConfig(unittest.TestCase):
    def setUp(self):
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = ['etc/nagios_1r_1h_1s.cfg']
        self.conf = Config()
        self.conf.read_config(self.config_files)
        self.conf.instance_id = 0
        self.conf.instance_name = 'test'
        self.conf.linkify_templates()
        self.conf.apply_inheritance()
        self.conf.explode()
        self.conf.create_reversed_list()
        self.conf.remove_twins()
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.clean_useless()
        self.conf.pythonize()
        self.conf.linkify()
        self.conf.apply_dependancies()
        self.conf.explode_global_conf()
        self.conf.is_correct()
        self.confs = self.conf.cut_into_parts()
        self.dispatcher = Dispatcher(self.conf, self.me)
        self.sched = Scheduler(None)
        m = MacroResolver()
        m.init(self.conf)
        self.sched.load_conf(self.conf)
        e = ExternalCommand(self.conf, 'applyer')
        self.sched.external_command = e
        e.load_scheduler(self.sched)
        self.sched.schedule()
    
    
    def add(self, b):
        self.broks[b.id] = b
    
    
    def fake_check(self, ref, exit_status, output="OK"):
        print "fake", ref
        now = time.time()
        ref.schedule()
        #now checks are schedule and we get them in
        #the action queue
        check = ref.actions.pop()
        self.sched.add(check)  # check is now in sched.checks[]
        # fake execution
        check.check_time = now
        check.output = output
        check.exit_status = exit_status
        check.execution_time = 0.001
        check.status = 'waitconsume'
        self.sched.waiting_results.append(check)


    def scheduler_loop(self, count, reflist):
        for ref in reflist:
            (obj, exit_status, output) = ref
            obj.checks_in_progress = []  
        for loop in range(1, count + 1):
            print "processing check", loop
            for ref in reflist:
                (obj, exit_status, output) = ref
                obj.update_in_checking()
                self.fake_check(obj, exit_status, output)
            self.sched.consume_results()
            self.sched.get_new_actions()
            self.sched.get_new_broks()
            self.worker_loop()
            for ref in reflist:
                (obj, exit_status, output) = ref
                obj.checks_in_progress = []
            self.sched.update_downtimes_and_comments()
            #time.sleep(ref.retry_interval * 60 + 1)
            time.sleep(60 + 1)


    def worker_loop(self):
        self.sched.delete_zombie_checks()
        self.sched.delete_zombie_actions()
        checks = self.sched.get_to_run_checks(True, False)
        actions = self.sched.get_to_run_checks(False, True)
        #print "------------ worker loop checks ----------------"
        #print checks
        #print "------------ worker loop actions ----------------"
        self.show_actions()
        #print "------------ worker loop new ----------------"
        for a in actions:
            a.status = 'inpoller'
            a.check_time = time.time()
            a.exit_status = 0
            self.sched.put_results(a)
        self.show_actions()
        #print "------------ worker loop end ----------------"

    
    def show_logs(self):
        print "--- logs <<<----------------------------------"
        for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
            if brok.type == 'log':
                print "LOG:", brok.data['log']
        print "--- logs >>>----------------------------------"
    
    
    def show_actions(self):
        print "--- actions <<<----------------------------------"
        for a in sorted(self.sched.actions.values(), lambda x, y: x.id - y.id):
            if a.is_a == 'notification':
                if a.ref.my_type == "host":
                    ref = "host: %s" % a.ref.get_name()
                else:
                    ref = "host: %s svc: %s" % (a.ref.host.get_name(), a.ref.get_name())
                print "NOTIFICATION %d %s %s %s" % (a.id, ref, time.asctime(time.localtime(a.t_to_go)), a.status)
            elif a.is_a == 'eventhandler':
                print "EVENTHANDLER:", a
        print "--- actions >>>----------------------------------"
    
    
    def show_and_clear_logs(self):
        self.show_logs()
        self.clear_logs()
    
    
    def show_and_clear_actions(self):
        self.show_actions()
        self.clear_actions()
    
    
    def count_logs(self):
        return len([b for b in self.sched.broks.values() if b.type == 'log'])
    
    
    def count_actions(self):
        return len(self.sched.actions.values())
    
    
    def clear_logs(self):
        id_to_del = []
        for b in self.sched.broks.values():
            if b.type == 'log':
                id_to_del.append(b.id)
        for id in id_to_del:
            del self.sched.broks[id]
    
    
    def clear_actions(self):
        self.sched.actions = {}
    
    
    def log_match(self, index, pattern):
        if index > self.count_logs():
            return False
        else:
            regex = re.compile(pattern)
            lognum = 1
            for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
                if brok.type == 'log':
                    if index == lognum:
                        if re.search(regex, brok.data['log']):
                            return True
                    lognum += 1
        return False


    def any_log_match(self, pattern):
        regex = re.compile(pattern)
        for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
            if brok.type == 'log':
                if re.search(regex, brok.data['log']):
                    return True
        return False


    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"
    
    
    

    def test_conf_is_correct(self):
        self.print_header()
        self.assert_(self.conf.conf_is_correct)


    def test_continuous_notifications(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']])
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assert_(svc.current_notification_number == 0)
        #--------------------------------------------------------------
        # service reaches soft;1
        # there must not be any notification
        #--------------------------------------------------------------
        print "- 1 x BAD get soft -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        # check_notification: not (soft)
        print "---current_notification_number", svc.current_notification_number
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created
        # notification number must be 1
        #--------------------------------------------------------------
        print "- 1 x BAD get hard -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
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
        print "---------------------------------1st round with a hard"
        print "find a way to get the number of the last reaction"
        cnn = svc.current_notification_number
        print "- 5 x BAD repeat -------------------------------------"
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        print "cnn and cur", cnn, svc.current_notification_number
        self.assert_(svc.current_notification_number > cnn)
        cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number > cnn)
        #--------------------------------------------------------------
        # 2 cycles = 2 minutes = 2 new notifications
        #--------------------------------------------------------------
        cnn = svc.current_notification_number
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number > cnn)
        #--------------------------------------------------------------
        # 2 cycles = 2 minutes = 2 new notifications (theoretically)
        # BUT: test_contact filters notifications
        # we do not raise current_notification_number if no mail was sent
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] DISABLE_CONTACT_SVC_NOTIFICATIONS;test_contact" % now
        self.sched.run_external_command(cmd)
        cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == cnn)
        #--------------------------------------------------------------
        # again a normal cycle
        # test_contact receives his mail
        #--------------------------------------------------------------
        now = time.time()
        cmd = "[%lu] ENABLE_CONTACT_SVC_NOTIFICATIONS;test_contact" % now
        self.sched.run_external_command(cmd)
        #cnn = svc.current_notification_number
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == cnn + 1)
        #--------------------------------------------------------------
        # now recover. there must be no scheduled/inpoller notification
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']])
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assert_(svc.current_notification_number == 0)


    def test_continuous_notifications_delayed(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.first_notification_delay = 5
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP']])
        #-----------------------------------------------------------------
        # initialize with a good check. there must be no pending notification
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assert_(svc.current_notification_number == 0)
        #-----------------------------------------------------------------
        # check fails and enters soft state.
        # there must be no notification, only the event handler
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 1, 'BAD']])
        self.assert_(self.count_actions() == 1)
        last_time_not_ok = svc.last_time_non_ok_or_up()
        deadline = svc.last_time_non_ok_or_up() + svc.first_notification_delay * svc.__class__.interval_length
        #-----------------------------------------------------------------
        # check fails again and enters hard state.
        # now there is a (scheduled for later) notification and an event handler
        # current_notification_number is still 0, until notifications
        # have actually been sent
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(svc.current_notification_number == 0)
        #-----------------------------------------------------------------
        # repeat bad checks during the delay time
        # there is 1 action which is the scheduled notification
        #-----------------------------------------------------------------
        loop=0
        while deadline > time.time():
            loop += 1
            self.scheduler_loop(1, [[svc, 2, 'BAD']])
            self.show_and_clear_logs()
            self.show_actions()
            ###self.assert_(self.count_actions() == 1)
        #-----------------------------------------------------------------
        # now the delay period is over and the notification can be sent
        # with the next bad check
        # there is 1 action, the notification (
        # 1 notification was sent, so current_notification_number is 1
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.assert_(self.count_actions() == 2)
        # 1 master, 1 child
        self.assert_(svc.current_notification_number == 1)
        self.show_actions()
        self.assert_(len(svc.notifications_in_progress) == 1) # master is zombieand removed_from_in_progress
        self.show_logs()
        self.assert_(self.log_match(1, 'SERVICE NOTIFICATION.*;CRITICAL;'))
        self.show_and_clear_logs()
        self.show_actions()
        #-----------------------------------------------------------------
        # relax with a successful check
        # there are 2 actions, one notification and one eventhandler
        # current_notification_number was reset to 0
        #-----------------------------------------------------------------
        self.scheduler_loop(2, [[svc, 0, 'GOOD']])
        self.assert_(self.log_match(1, 'SERVICE ALERT.*;OK;'))
        self.assert_(self.log_match(2, 'SERVICE EVENT HANDLER.*;OK;'))
        self.assert_(self.log_match(3, 'SERVICE NOTIFICATION.*;OK;'))
        # evt reap 2 loops
        self.assert_(svc.current_notification_number == 0)
        self.assert_(len(svc.notifications_in_progress) == 0)
        self.assert_(len(svc.notified_contacts) == 0)
        #self.assert_(self.count_actions() == 2)
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
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.first_notification_delay = 5
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP']])
        #-----------------------------------------------------------------
        # initialize with a good check. there must be no pending notification
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assert_(svc.current_notification_number == 0)
        #-----------------------------------------------------------------
        # check fails and enters soft state.
        # there must be no notification, only the event handler
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 1, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(self.count_actions() == 1)
        #-----------------------------------------------------------------
        # check fails again and enters hard state.
        # now there is a (scheduled for later) notification and an event handler
        # current_notification_number is still 0 (will be raised when
        # a notification is actually sent)
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(self.count_actions() == 2)
        self.assert_(svc.current_notification_number == 0)
        #-----------------------------------------------------------------
        # repeat bad checks during the delay time
        # but only one time. we don't want to reach the deadline
        # there is one action: the pending notification
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        self.show_actions()
        self.assert_(self.count_actions() == 1)
        #-----------------------------------------------------------------
        # relax with a successful check
        # there is 1 action, the eventhandler. 
        # there is a second action: the master recover notification
        # but it becomes a zombie very soon, because it has no effect
        #-----------------------------------------------------------------
        self.scheduler_loop(1, [[svc, 0, 'GOOD']])
        self.assert_(self.log_match(1, 'SERVICE ALERT.*;OK;'))
        self.assert_(self.log_match(2, 'SERVICE EVENT HANDLER.*;OK;'))
        self.assert_(not self.log_match(3, 'SERVICE NOTIFICATION.*;OK;'))
        self.show_actions()
        self.assert_(len(svc.notifications_in_progress) == 0)
        self.assert_(len(svc.notified_contacts) == 0)
        self.assert_(self.count_actions() == 2)
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
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0") 
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP'], [svc, 0, 'OK']])
        self.assert_(svc.current_notification_number == 0)
        #--------------------------------------------------------------
        # service reaches hard;2
        # a notification must have been created
        # notification number must be 1
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[host, 0, 'UP'], [svc, 2, 'BAD']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.log_match(1, 'SERVICE ALERT.*;CRITICAL;SOFT'))
        self.assert_(self.log_match(2, 'SERVICE EVENT HANDLER.*;CRITICAL;SOFT'))
        self.assert_(self.log_match(3, 'SERVICE ALERT.*;CRITICAL;HARD'))
        self.assert_(self.log_match(4, 'SERVICE EVENT HANDLER.*;CRITICAL;HARD'))
        self.assert_(self.log_match(5, 'SERVICE NOTIFICATION.*;CRITICAL;'))
        self.assert_(svc.current_notification_number == 1)
        self.clear_logs()
        self.clear_actions()
        #--------------------------------------------------------------
        # reset host/service state
        #--------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP'], [svc, 0, 'OK']])
        self.assert_(svc.current_notification_number == 0)
        duration = 300
        now = time.time()
        # fixed downtime valid for the next 5 minutes
        cmd = "[%lu] SCHEDULE_HOST_DOWNTIME;test_host_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        #--------------------------------------------------------------
        # service reaches hard;2
        # no notificatio
        #--------------------------------------------------------------
        self.scheduler_loop(2, [[host, 0, 'UP'], [svc, 2, 'BAD']])
        self.assert_(self.any_log_match('HOST NOTIFICATION.*;DOWNTIMESTART'))
        self.assert_(not self.any_log_match('SERVICE NOTIFICATION.*;CRITICAL;'))
        self.show_and_clear_logs()
        self.show_and_clear_actions()


    def todo_test_notification_outside_notification_period(self):
        self.print_header()
        # create notification_period which ends 5 min ago and starts in 5 min 
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(1, [[host, 0, 'UP']])
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.show_and_clear_logs()
        self.show_and_clear_actions()
        self.assert_(svc.current_notification_number == 0)
        #-----------------------------------------------------------------
        # we are outside the service.notification_period
        # the service reaches a hard state and a notification is
        # scheduled but not sent yet
        #-----------------------------------------------------------------
        print "- 2 x BAD get hard -------------------------------------"
        self.scheduler_loop(2, [[svc, 2, 'BAD']])
        # check action array: 1xnotification, check logs: none
        print "---current_notification_number", svc.current_notification_number
        #-----------------------------------------------------------------
        # execute more checks with a bad result.
        # we re-enter the notification_period and finally 
        # a notification is sent (a log exists, next notification is scheduled
        #-----------------------------------------------------------------
        self.scheduler_loop(6, [[svc, 2, 'BAD']])
        self.show_and_clear_logs()
        #self.show_and_clear_actions()
        self.show_actions()
        # check_notification: yes (hard)
        print "---current_notification_number", svc.current_notification_number
        # notification_number is already sent. the next one has been scheduled
        # and is waiting for notification_interval to pass. so the current
        # number is 2
        self.assert_(svc.current_notification_number == 1)
        #-----------------------------------------------------------------
        # execute a good check.
        # expect a recover notification with number 0 
        # a recover log for test_contact is written
        #-----------------------------------------------------------------
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assert_(len(svc.notifications_in_progress) == 1)
        self.show_and_clear_logs()
        self.show_actions()
        #-----------------------------------------------------------------
        # again execute a good check.
        # neither a notification nor a log must be found 
        #-----------------------------------------------------------------
        print "- 1 x OK -------------------------------------"
        self.scheduler_loop(1, [[svc, 0, 'OK']])
        self.assert_(len(svc.notifications_in_progress) == 0)
        self.show_and_clear_logs()
        self.show_actions()


if __name__ == '__main__':
    unittest.main()
