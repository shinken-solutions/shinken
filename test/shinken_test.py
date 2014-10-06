#!/usr/bin/env python

#
# This file is used to test host- and service-downtimes.
#

import sys
import time
import datetime
import os
import string
import re
import random
import unittest
import copy

# import the shinken library from the parent directory
import __import_shinken ; del __import_shinken

import shinken
from shinken.objects.config import Config
from shinken.objects.command import Command
from shinken.objects.module import Module

from shinken.dispatcher import Dispatcher
from shinken.log import logger
from shinken.modulesctx import modulesctx
from shinken.scheduler import Scheduler
from shinken.macroresolver import MacroResolver
from shinken.external_command import ExternalCommandManager, ExternalCommand
from shinken.check import Check
from shinken.message import Message
from shinken.arbiterlink import ArbiterLink
from shinken.schedulerlink import SchedulerLink
from shinken.pollerlink import PollerLink
from shinken.reactionnerlink import ReactionnerLink
from shinken.brokerlink import BrokerLink
from shinken.satellitelink import SatelliteLink
from shinken.notification import Notification
from shinken.modulesmanager import ModulesManager
from shinken.basemodule import BaseModule

from shinken.brok import Brok
from shinken.misc.common import DICT_MODATTR

from shinken.daemons.schedulerdaemon import Shinken
from shinken.daemons.brokerdaemon import Broker
from shinken.daemons.arbiterdaemon import Arbiter
from shinken.daemons.receiverdaemon import Receiver
from logging import ERROR

# Modules are by default on the ../modules
myself = os.path.abspath(__file__)

global modules_dir
modules_dir = "modules"

def define_modules_dir(val):
    global modules_dir
    modules_dir = val

class __DUMMY:
    def add(self, obj):
        pass

logger.load_obj(__DUMMY())
logger.setLevel(ERROR)


# We overwrite the functions time() and sleep()
# This way we can modify sleep() so that it immediately returns although
# for a following time() it looks like thee was actually a delay.
# This massively speeds up the tests.
class TimeHacker(object):

    def __init__(self):
        self.my_offset = 0
        self.my_starttime = time.time()
        self.my_oldtime = time.time
        self.original_time_time = time.time
        self.original_time_sleep = time.sleep
        self.in_real_time = True

    def my_time_time(self):
        return self.my_oldtime() + self.my_offset

    def my_time_sleep(self, delay):
        self.my_offset += delay

    def time_warp(self, duration):
        self.my_offset += duration

    def set_my_time(self):
        if self.in_real_time:
            time.time = self.my_time_time
            time.sleep = self.my_time_sleep
            self.in_real_time = False

# If external processes or time stamps for files are involved, we must
# revert the fake timing routines, because these externals cannot be fooled.
# They get their times from the operating system.
    def set_real_time(self):
        if not self.in_real_time:
            time.time = self.original_time_time
            time.sleep = self.original_time_sleep
            self.in_real_time = True


#Time hacking for every test!
time_hacker = TimeHacker()
time_hacker.set_my_time()


class Pluginconf(object):
    pass


class _Unittest2CompatMixIn:
    """
    Mixin for simulating methods new in unittest2 resp. Python 2.7.

    Every test-case should inherit this *after* unittest.TestCase to
    make the compatiblity-methods available if they are not defined in
    unittest.TestCase already. Example::

       class MyTestCase(unittest.TestCase, Unittest2CompatMixIn):
           ...
    In our case, it's better to always inherit from ShinkenTest

    """
    def assertNotIn(self, member, container, msg=None):
       self.assertTrue(member not in container)

    def assertIn(self, member, container, msg=None):
        self.assertTrue(member in container)

    def assertIsInstance(self, obj, cls, msg=None):
        self.assertTrue(isinstance(obj, cls))

    def assertRegexpMatches(self, line, pattern):
        r = re.search(pattern, line)
        self.assertTrue(r is not None)

    def assertIs(self, obj, cmp, msg=None):
        self.assertTrue(obj is cmp)


class ShinkenTest(unittest.TestCase, _Unittest2CompatMixIn):
    def setUp(self):
        self.setup_with_file('etc/shinken_1r_1h_1s.cfg')

    def setup_with_file(self, path):
        time_hacker.set_my_time()
        self.print_header()
        # i am arbiter-like
        self.broks = {}
        self.me = None
        self.log = logger
        self.log.load_obj(self)
        self.config_files = [path]
        self.conf = Config()
        buf = self.conf.read_config(self.config_files)
        raw_objects = self.conf.read_config_buf(buf)
        self.conf.create_objects_for_type(raw_objects, 'arbiter')
        self.conf.create_objects_for_type(raw_objects, 'module')
        self.conf.early_arbiter_linking()
        self.conf.create_objects(raw_objects)
        self.conf.instance_id = 0
        self.conf.instance_name = 'test'
        # Hack push_flavor, that is set by the dispatcher
        self.conf.push_flavor = 0
        self.conf.load_triggers()
        #import pdb;pdb.set_trace()
        self.conf.linkify_templates()
        #import pdb;pdb.set_trace()
        self.conf.apply_inheritance()
        #import pdb;pdb.set_trace()
        self.conf.explode()
        #print "Aconf.services has %d elements" % len(self.conf.services)
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.remove_templates()
        self.conf.compute_hash()
        #print "conf.services has %d elements" % len(self.conf.services)
        self.conf.override_properties()
        self.conf.linkify()
        self.conf.apply_dependencies()
        self.conf.explode_global_conf()
        self.conf.propagate_timezone_option()
        self.conf.create_business_rules()
        self.conf.create_business_rules_dependencies()
        self.conf.is_correct()
        if not self.conf.conf_is_correct:
            print "The conf is not correct, I stop here"
            self.conf.dump()
            return
        self.conf.clean()

        self.confs = self.conf.cut_into_parts()
        self.conf.prepare_for_sending()
        self.conf.show_errors()
        self.dispatcher = Dispatcher(self.conf, self.me)

        scheddaemon = Shinken(None, False, False, False, None, None)
        self.sched = Scheduler(scheddaemon)

        scheddaemon.sched = self.sched
        scheddaemon.modules_dir = modules_dir
        scheddaemon.load_modules_manager()
        # Remember to clean the logs we just created before launching tests
        self.clear_logs()
        m = MacroResolver()
        m.init(self.conf)
        self.sched.load_conf(self.conf, in_test=True)
        e = ExternalCommandManager(self.conf, 'applyer')
        self.sched.external_command = e
        e.load_scheduler(self.sched)
        e2 = ExternalCommandManager(self.conf, 'dispatcher')
        e2.load_arbiter(self)
        self.external_command_dispatcher = e2
        self.sched.conf.accept_passive_unknown_check_results = False

        self.sched.schedule()

    def add(self, b):
        if isinstance(b, Brok):
            self.broks[b.id] = b
            return
        if isinstance(b, ExternalCommand):
            self.sched.run_external_command(b.cmd_line)

    def fake_check(self, ref, exit_status, output="OK"):
        #print "fake", ref
        now = time.time()
        ref.schedule(force=True)
        # now checks are schedule and we get them in
        # the action queue
        #check = ref.actions.pop()
        check = ref.checks_in_progress[0]
        self.sched.add(check)  # check is now in sched.checks[]

        # Allows to force check scheduling without setting its status nor
        # output. Useful for manual business rules rescheduling, for instance.
        if exit_status is None:
            return

        # fake execution
        check.check_time = now

        # and lie about when we will launch it because
        # if not, the schedule call for ref
        # will not really reschedule it because there
        # is a valid value in the future
        ref.next_chk = now - 0.5

        check.get_outputs(output, 9000)
        check.exit_status = exit_status
        check.execution_time = 0.001
        check.status = 'waitconsume'
        self.sched.waiting_results.append(check)


    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61, verbose=True):
        for ref in reflist:
            (obj, exit_status, output) = ref
            obj.checks_in_progress = []
        for loop in range(1, count + 1):
            if verbose is True:
                print "processing check", loop
            for ref in reflist:
                (obj, exit_status, output) = ref
                obj.update_in_checking()
                self.fake_check(obj, exit_status, output)
            self.sched.manage_internal_checks()

            self.sched.consume_results()
            self.sched.get_new_actions()
            self.sched.get_new_broks()
            self.sched.scatter_master_notifications()
            self.worker_loop(verbose)
            for ref in reflist:
                (obj, exit_status, output) = ref
                obj.checks_in_progress = []
            self.sched.update_downtimes_and_comments()
            #time.sleep(ref.retry_interval * 60 + 1)
            if do_sleep:
                time.sleep(sleep_time)


    def worker_loop(self, verbose=True):
        self.sched.delete_zombie_checks()
        self.sched.delete_zombie_actions()
        checks = self.sched.get_to_run_checks(True, False, worker_name='tester')
        actions = self.sched.get_to_run_checks(False, True, worker_name='tester')
        #print "------------ worker loop checks ----------------"
        #print checks
        #print "------------ worker loop actions ----------------"
        if verbose is True:
            self.show_actions()
        #print "------------ worker loop new ----------------"
        for a in actions:
            a.status = 'inpoller'
            a.check_time = time.time()
            a.exit_status = 0
            self.sched.put_results(a)
        if verbose is True:
            self.show_actions()
        #print "------------ worker loop end ----------------"


    def show_logs(self):
        print "--- logs <<<----------------------------------"
        if hasattr(self, "sched"):
            broks = self.sched.broks
        else:
            broks = self.broks
        for brok in sorted(broks.values(), lambda x, y: x.id - y.id):
            if brok.type == 'log':
                brok.prepare()
                print "LOG:", brok.data['log'].encode("utf-8")
        print "--- logs >>>----------------------------------"


    def show_actions(self):
        print "--- actions <<<----------------------------------"
        if hasattr(self, "sched"):
            actions = self.sched.actions
        else:
            actions = self.actions
        for a in sorted(actions.values(), lambda x, y: x.id - y.id):
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
        if hasattr(self, "sched"):
            broks = self.sched.broks
        else:
            broks = self.broks
        return len([b for b in broks.values() if b.type == 'log'])


    def count_actions(self):
        if hasattr(self, "sched"):
            actions = self.sched.actions
        else:
            actions = self.actions
        return len(actions.values())


    def clear_logs(self):
        if hasattr(self, "sched"):
            broks = self.sched.broks
        else:
            broks = self.broks
        id_to_del = []
        for b in broks.values():
            if b.type == 'log':
                id_to_del.append(b.id)
        for id in id_to_del:
            del broks[id]


    def clear_actions(self):
        if hasattr(self, "sched"):
            self.sched.actions = {}
        else:
            self.actions = {}


    def log_match(self, index, pattern):
        # log messages are counted 1...n, so index=1 for the first message
        if index > self.count_logs():
            return False
        else:
            regex = re.compile(pattern)
            lognum = 1
            for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
                if brok.type == 'log':
                    brok.prepare()
                    if index == lognum:
                        if re.search(regex, brok.data['log']):
                            return True
                    lognum += 1
        return False

    def any_log_match(self, pattern):
        regex = re.compile(pattern)
        if hasattr(self, "sched"):
            broks = self.sched.broks
        else:
            broks = self.broks
        for brok in sorted(broks.values(), lambda x, y: x.id - y.id):
            if brok.type == 'log':
                brok.prepare()
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
        print "\n" + "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def xtest_conf_is_correct(self):
        self.print_header()
        self.assert_(self.conf.conf_is_correct)





if __name__ == '__main__':
    unittest.main()
