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


    def test_conf_is_correct(self):
        self.assert_(self.conf.conf_is_correct)


    def test_schedule_flexible_svc_downtime_and_statusdat(self):
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
        time.sleep(20)

        print "downtime was scheduled. check its inactivity and the comment"
        self.assert_(svc.downtimes[0] in self.sched.downtimes.values() and len(self.sched.downtimes) == 1)
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        self.assert_(svc.comments[0] in self.sched.comments.values() and len(self.sched.comments) == 1)
        self.assert_(svc.downtimes[0].comment_id == svc.comments[0].id)

        svc.update_in_checking()

        self.fake_check(svc, 0, 'OK')
        self.sched.consume_results()

        print "good check was launched, downtime must still be inactive"
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(not svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)
        time.sleep(61)

        # now the downtime must be triggered
        self.fake_check(svc, 2, 'BAD')
        self.sched.consume_results()

        print "bad check was launched, downtime must now be active"
        print svc.downtimes[0]
        self.assert_(not svc.downtimes[0].fixed)
        self.assert_(svc.downtimes[0].is_in_effect)
        self.assert_(not svc.downtimes[0].can_be_deleted)


        for brok in self.sched.broks.values():
            if brok.type == 'log':
                print "LOG:", brok.data['log']



if __name__ == '__main__':
    unittest.main()
