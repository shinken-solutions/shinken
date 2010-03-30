#!/usr/bin/env python2.6

#
# This file is used to test host- and service-downtimes.
#

import sys
import time
import os
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


    def show_logs(self):
        for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
            if brok.type == 'log':
                print "LOGID", brok.id
                print "LOG:", brok.data['log']


    def show_actions(self):
        for a in sorted(self.sched.actions.values(), lambda x, y: x.id - y.id):
            print "ACTION:", a


    def count_logs(self):
        return len([b for b in self.sched.broks.values() if b.type == 'log'])

    
    def count_actions(self):
        return len(self.sched.actions.values())


    def clear_logs(self):
        print "--------- clear_logs enter ---------- with", self.count_logs()
        id_to_del = []
        for b in self.sched.broks.values():
            if b.type == 'log':
                print ">>id_to_del+", b.id
                id_to_del.append(b.id)
        for id in id_to_del:
            del self.sched.broks[id]
        for b in self.sched.broks.values():
            if b.type == 'log':
                print "<<id_to_del+", b.id
        print "--------- clear_logs leave ----------with", self.count_logs()
            

    def clear_actions(self):
        self.sched.actions = {}


    def scheduler_loop(self, count, ref, exit_status, output="OK"):
        ref.checks_in_progress = []
        for loop in range(1, count):
            print "processing check", loop
            ref.update_in_checking()
            self.fake_check(ref, exit_status, output)
            self.sched.consume_results()
            ref.checks_in_progress = []
            self.sched.update_downtimes_and_comments()
            time.sleep(ref.retry_interval * 60 + 1)


    def test_conf_is_correct(self):
        self.assert_(self.conf.conf_is_correct)


    def test_schedule_fixed_svc_downtime(self):
        # schedule a 2-minute downtime
        # downtime must be active
        # consume a good result, sleep for a minute
        # downtime must be active
        # consume a bad result
        # downtime must be active
        # no notification must be found in broks
        duration = 180
        now = time.time()
        # downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        time.sleep(20)
        self.sched.update_downtimes_and_comments()

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

        svc.update_in_checking()

        self.fake_check(svc, 0, 'OK')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()

        print "good check was launched, downtime must be active"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.is_in_downtime)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        time.sleep(61)

        self.fake_check(svc, 2, 'BAD')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()

        print "bad check was launched (SOFT;1), downtime must be active"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.is_in_downtime)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        time.sleep(61)

        # now the state changes to hard
        self.fake_check(svc, 2, 'BAD')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()

        print "bad check was launched (HARD;2), downtime must be active"
        print svc.downtimes[0]
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.is_in_downtime)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)

        scheduled_downtime_depth = svc.scheduled_downtime_depth
        cmd = "[%lu] DEL_SVC_DOWNTIME;%d" % (now, svc.downtimes[0].id)
        self.sched.run_external_command(cmd)
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(not svc.is_in_downtime)
        self.assert_(svc.scheduled_downtime_depth < scheduled_downtime_depth)
        self.assert_(svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(svc.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(svc.comments) == 1)
        time.sleep(61)

        # now a notification must be sent
        self.fake_check(svc, 2, 'BAD')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()
        # downtimes must have been deleted now
        self.assert_(len(self.sched.downtimes) == 0)
        self.assert_(len(svc.downtimes) == 0)
        self.assert_(len(self.sched.comments) == 0)
        self.assert_(len(svc.comments) == 0)

    def test_schedule_flexible_svc_downtime(self):
        # schedule a 2-minute downtime
        # downtime must not be active
        # consume a good result, sleep for a minute
        # downtime must not be active
        # consume a bad result
        # downtime must be active
        # no notification must be found in broks
        duration = 180
        now = time.time()
        # flexible downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_SVC_DOWNTIME;test_host_0;test_ok_0;%d;%d;0;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        time.sleep(20)

        print "downtime was scheduled. check its inactivity and the comment"
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

        svc.update_in_checking()

        self.fake_check(svc, 0, 'OK')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()

        print "good check was launched, downtime must still be inactive"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(not svc.is_in_downtime)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        time.sleep(61)

        self.fake_check(svc, 2, 'BAD')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()

        print "bad check was launched (SOFT;1), downtime must still be inactive"
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(not svc.is_in_downtime)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        time.sleep(61)

        # now the downtime must be triggered
        self.fake_check(svc, 2, 'BAD')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()

        print "bad check was launched (HARD;2), downtime must now be active"
        print svc.downtimes[0]
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values())
        self.assert_(svc.is_in_downtime)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)

        scheduled_downtime_depth = svc.scheduled_downtime_depth
        cmd = "[%lu] DEL_SVC_DOWNTIME;%d" % (now, svc.downtimes[0].id)
        self.sched.run_external_command(cmd)
        self.assert_(len(self.sched.downtimes) == 1)
        self.assert_(len(svc.downtimes) == 1)
        self.assert_(not svc.is_in_downtime)
        self.assert_(svc.scheduled_downtime_depth < scheduled_downtime_depth)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(svc.downtimes[0].can_be_deleted)
        self.assert_(len(self.sched.comments) == 1)
        self.assert_(len(svc.comments) == 1)
        time.sleep(61)

        # now a notification must be sent
        self.fake_check(svc, 2, 'BAD')
        self.sched.consume_results()
        self.sched.update_downtimes_and_comments()
        # downtimes must have been deleted now
        self.assert_(len(self.sched.downtimes) == 0)
        self.assert_(len(svc.downtimes) == 0)
        self.assert_(len(self.sched.comments) == 0)
        self.assert_(len(svc.comments) == 0)

        self.show_logs()
        self.show_actions()


    def test_schedule_fixed_host_downtime(self):
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
        print "show logs and actions"
        self.show_logs()
        self.show_actions()
        self.assert_(self.count_logs() == 0)
        self.assert_(self.count_actions() == 0)
        print "now run three service checks with a critical result which is more than enough. (max 2)"
        #self.scheduler_loop(4, host, 2, 'DOWN')
        self.scheduler_loop(3, svc, 2, 'CRITICAL')
        print "show logs and actions after three negative checkresults"
        print "there must be a notification"
        # count actions and notifications
        self.show_logs()
        self.show_actions()
        # soft 1, eventhandler, hard 2, notification, eventhandler
        self.assert_(self.count_logs() == 5)
        # eventhandler, notification, eventhandler
        self.assert_(self.count_actions() == 3)

        print "clear logs and actions and recover the service"
        self.clear_logs()
        self.clear_actions()
        self.assert_(self.count_logs() == 0)
        self.assert_(self.count_actions() == 0)
        self.scheduler_loop(2, svc, 0, 'OK')
        # count actions and notifications
        self.show_logs()
        self.show_actions()
        # hard 1, notification, eventhandler
        self.assert_(self.count_logs() == 3)
        # notification, eventhandler
        self.assert_(self.count_actions() == 2)
        print "------------------------------------------------------"
        
        self.clear_logs()
        self.clear_actions()
        self.assert_(self.count_logs() == 0)
        self.assert_(self.count_actions() == 0)
        duration = 600
        now = time.time()
        # flexible downtime valid for the next 2 minutes
        cmd = "[%lu] SCHEDULE_HOST_DOWNTIME;test_host_0;%d;%d;1;0;%d;lausser;blablub" % (now, now, now + duration, duration)
        self.sched.run_external_command(cmd)
        time.sleep(20)
        self.sched.update_downtimes_and_comments()

        print "downtime was scheduled. check its inactivity and the comment"
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
        self.scheduler_loop(5, host, 2, 'DOWN')
        print "host is down and in hard state. and inside a downtime"
        self.show_logs()
        self.show_actions()
        # start downtime, soft 1, soft 2, hard 3, 
        self.assert_(self.count_logs() == 4)
        # nothing
        self.assert_(self.count_actions() == 0)

        # send host into downtime
        # run host checks with result down
        # check for notifications (there must be no notification)

        # send host into downtime
        # run service checks with result critical
        # check for notifications (there must be no notification)


        # todo
        # checks return 1=warn. this means normally up
        # set use_aggressive_host_checking which treats warn as down



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
