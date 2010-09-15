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
sys.path.append("..")
sys.path.append("../shinken")
from shinken.config import Config
from shinken.dispatcher import Dispatcher
from shinken.log import Log
from shinken.scheduler import Scheduler
from shinken.macroresolver import MacroResolver
from shinken.external_command import ExternalCommandManager
from shinken.check import Check
from shinken.module import Module

class ShinkenTest(unittest.TestCase):
    def setUp(self):
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')

    def setup_with_file(self, path):
        # i am arbiter-like
        Config.fill_usern_macros()
        self.broks = {}
        self.me = None
        self.log = Log()
        self.log.load_obj(self)
        self.config_files = [path]
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
        e = ExternalCommandManager(self.conf, 'applyer')
        self.sched.external_command = e
        e.load_scheduler(self.sched)
        self.sched.schedule()
    
    
    def add(self, b):
        self.broks[b.id] = b
    
    
    def fake_check(self, ref, exit_status, output="OK"):
        #print "fake", ref
        now = time.time()
        ref.schedule(force=True)
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


    def scheduler_loop(self, count, reflist, do_sleep=False):
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
            if do_sleep:
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
                print "NOTIFICATION %d %s %s %s %s" % (a.id, ref, a.type, time.asctime(time.localtime(a.t_to_go)), a.status)
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
        # log messages are counted 1...n, so index=1 for the first message
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


    def get_log_match(self, pattern):
        regex = re.compile(pattern)
        res = []
        for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
            if brok.type == 'log':
                if re.search(regex, brok.data['log']):
                    res.append(brok.data['log'])
        return res



    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"
    
    
    

    def xtest_conf_is_correct(self):
        self.print_header()
        self.assert_(self.conf.conf_is_correct)



if __name__ == '__main__':
    unittest.main()
