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
        check = ref.schedule()
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
        #self.show_actions()
        #print "------------ worker loop new ----------------"
        for a in actions:
            #print "---> fake return of action", a.id
            a.status = 'inpoller'
            a.check_time = time.time()
            a.exit_status = 0
            self.sched.put_results(a)
        #self.show_actions()
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
        svc.act_depend_of = [] # no hostchecks on critical checkresults
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
        svc.act_depend_of = [] # no hostchecks on critical checkresults
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
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
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
        self.worker_loop() # push the downtime notification
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
        self.assert_(self.count_logs() == 2)    # start downt, notif downt
        self.assert_(self.count_actions() == 2) # notif" down
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
        self.assert_(self.count_actions() == 1) # evt1
        self.clear_logs()
        #--
        self.scheduler_loop(1, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 2)    # soft2, evt2
        self.assert_(self.count_actions() == 1) # evt2
        self.clear_logs()
        #--
        self.scheduler_loop(1, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3)    # hard3, evt3, notif
        self.assert_(self.count_actions() == 3) # evt3, notif"
        self.clear_logs()
        #--
        self.scheduler_loop(1, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 1)    # next notif
        self.assert_(self.count_actions() == 2) # notif"
        self.clear_logs()
        #----------------------------------------------------------------
        # the host comes UP again
        # check log messages, (no) notifications and eventhandlers
        # only a blind recover notification
        #----------------------------------------------------------------
        self.scheduler_loop(1, [[host, 0, 'UP']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 3)    # hard3ok, evtok, notif
        self.assert_(self.count_actions() == 3) # evtok, notif"
        self.clear_logs()
        self.clear_actions()


    def test_schedule_fixed_host_downtime_with_service(self):
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
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
        self.worker_loop() # push the downtime notification
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
        self.scheduler_loop(4, [[host, 2, 'DOWN']])
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 9)    # start downt, notif downt, soft1, evt1, soft 2, evt2, hard 3, evt3, notif
        self.clear_logs()
        self.clear_actions()
        #----------------------------------------------------------------
        # now the service becomes critical
        # check that the host has a downtime, _not_ the service
        # check logs, (no) notifications and eventhandlers
        #----------------------------------------------------------------
        self.scheduler_loop(4, [[svc, 2, 'CRITICAL']])
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
        self.scheduler_loop(2, [[host, 0, 'UP']])
        self.show_logs()
        self.show_actions()
        # hard 3, eventhandler
        self.assert_(self.count_logs() == 3)    # up, evt, notif
        self.clear_logs()
        self.clear_actions()
        #----------------------------------------------------------------
        # the service becomes OK again
        # check log messages, (no) notifications and eventhandlers
        # check if the stop downtime notification is the only one
        #----------------------------------------------------------------
        self.scheduler_loop(10, [[host, 0, 'UP']])
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
