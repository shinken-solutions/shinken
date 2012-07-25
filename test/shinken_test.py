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

sys.path.append("..")
sys.path.append("../shinken")
#sys.path.append("../bin")
#sys.path.append(os.path.abspath("bin"))

import shinken
from shinken.objects.config import Config
from shinken.objects.command import Command
from shinken.objects.module import Module

from shinken.dispatcher import Dispatcher
from shinken.log import logger
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

from shinken.daemons.schedulerdaemon import Shinken
from shinken.daemons.brokerdaemon import Broker
from shinken.daemons.arbiterdaemon import Arbiter

from shinken.modules import livestatus_broker
from shinken.modules.livestatus_broker import LiveStatus_broker
from shinken.modules.livestatus_broker.livestatus import LiveStatus
from shinken.modules.livestatus_broker.livestatus_regenerator import LiveStatusRegenerator
from shinken.modules.livestatus_broker.livestatus_query_cache import LiveStatusQueryCache
from shinken.misc.datamanager import datamgr

livestatus_modconf = Module()
livestatus_modconf.module_name = "livestatus"
livestatus_modconf.module_type = livestatus_broker.properties['type']
livestatus_modconf.properties = livestatus_broker.properties.copy()

# We overwrite the functions time() and sleep()
# This way we can modify sleep() so that it immediately returns although
# for a following time() it looks like thee was actually a delay.
# This massively speeds up the tests.

time.my_offset = 0
time.my_starttime = time.time()
time.my_oldtime = time.time


def my_time_time():
    now = time.my_oldtime() + time.my_offset
    return now

original_time_time = time.time
time.time = my_time_time


def my_time_sleep(delay):
    time.my_offset += delay

original_time_sleep = time.sleep
time.sleep = my_time_sleep


def time_warp(duration):
    time.my_offset += duration

# If external processes or time stamps for files are involved, we must
# revert the fake timing routines, because these externals cannot be fooled.
# They get their times from the operating system.
# In this case we write the following lines in the test files:
#
# from shinken_test import *
# # we have an external process, so we must un-fake time functions
# time.time = original_time_time
# time.sleep = original_time_sleep

class Pluginconf(object):
    pass


class ShinkenTest(unittest.TestCase):
    def setUp(self):
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')

    def setup_with_file(self, path):
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
        self.conf.old_properties_names_to_new()
        self.conf.instance_id = 0
        self.conf.instance_name = 'test'
        # Hack push_flavor, that is set by the dispatcher
        self.conf.push_flavor = 0
        self.conf.load_triggers()
        self.conf.linkify_templates()
        self.conf.apply_inheritance()
        self.conf.explode()
        #print "Aconf.services has %d elements" % len(self.conf.services)
        self.conf.create_reversed_list()
        self.conf.remove_twins()
        self.conf.apply_implicit_inheritance()
        self.conf.fill_default()
        self.conf.remove_templates()
        self.conf.compute_hash()
        #print "conf.services has %d elements" % len(self.conf.services)
        self.conf.create_reversed_list()
        self.conf.pythonize()
        self.conf.linkify()
        self.conf.apply_dependencies()
        self.conf.explode_global_conf()
        self.conf.propagate_timezone_option()
        self.conf.create_business_rules()
        self.conf.create_business_rules_dependencies()
        self.conf.is_correct()
        if not self.conf.conf_is_correct:
            print "The conf is not correct, I stop here"
            return

        self.confs = self.conf.cut_into_parts()
        self.conf.prepare_for_sending()
        self.conf.show_errors()
        self.dispatcher = Dispatcher(self.conf, self.me)

        scheddaemon = Shinken(None, False, False, False, None)
        self.sched = Scheduler(scheddaemon)

        scheddaemon.sched = self.sched

        m = MacroResolver()
        m.init(self.conf)
        self.sched.load_conf(self.conf, in_test=True)
        e = ExternalCommandManager(self.conf, 'applyer')
        self.sched.external_command = e
        e.load_scheduler(self.sched)
        e2 = ExternalCommandManager(self.conf, 'dispatcher')
        e2.load_arbiter(self)
        self.external_command_dispatcher = e2

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
        check = ref.actions.pop()
        self.sched.add(check)  # check is now in sched.checks[]
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

    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        for ref in reflist:
            (obj, exit_status, output) = ref
            obj.checks_in_progress = []
        for loop in range(1, count + 1):
            print "processing check", loop
            for ref in reflist:
                (obj, exit_status, output) = ref
                obj.update_in_checking()
                self.fake_check(obj, exit_status, output)
            self.sched.manage_internal_checks()
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
                time.sleep(sleep_time)

    def worker_loop(self):
        self.sched.delete_zombie_checks()
        self.sched.delete_zombie_actions()
        checks = self.sched.get_to_run_checks(True, False, worker_name='tester')
        actions = self.sched.get_to_run_checks(False, True, worker_name='tester')
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
                brok.prepare()
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
                    brok.prepare()
                    if index == lognum:
                        if re.search(regex, brok.data['log']):
                            return True
                    lognum += 1
        return False

    def any_log_match(self, pattern):
        regex = re.compile(pattern)
        for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
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
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def xtest_conf_is_correct(self):
        self.print_header()
        self.assert_(self.conf.conf_is_correct)

    def find_modules_path(self):
        """ Find the absolute path of the shinken module directory and returns it.  """
        import shinken

        # BEWARE: this way of finding path is good if we still
        # DO NOT HAVE CHANGE PWD!!!
        # Now get the module path. It's in fact the directory modules
        # inside the shinken directory. So let's find it.

        print "modulemanager file", shinken.modulesmanager.__file__
        modulespath = os.path.abspath(shinken.modulesmanager.__file__)
        print "modulemanager absolute file", modulespath
        # We got one of the files of
        parent_path = os.path.dirname(os.path.dirname(modulespath))
        modulespath = os.path.join(parent_path, 'shinken', 'modules')
        print("Using modules path: %s" % (modulespath))

        return modulespath

    def do_load_modules(self):
        self.modules_manager.load_and_init()
        self.log.log("I correctly loaded the modules: [%s]" % (','.join([inst.get_name() for inst in self.modules_manager.instances])))

    def init_livestatus(self, modconf=None):
        self.livelogs = 'tmp/livelogs.db' + self.testid

        if modconf is None:
            modconf = Module({'module_name': 'LiveStatus',
                'module_type': 'livestatus',
                'port': str(50000 + os.getpid()),
                'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
                'host': '127.0.0.1',
                'socket': 'live',
                'name': 'test', #?
            })

        dbmodconf = Module({'module_name': 'LogStore',
            'module_type': 'logstore_sqlite',
            'use_aggressive_sql': "0",
            'database_file': self.livelogs,
            'archive_path': os.path.join(os.path.dirname(self.livelogs), 'archives'),
        })
        modconf.modules = [dbmodconf]
        self.livestatus_broker = LiveStatus_broker(modconf)
        self.livestatus_broker.create_queues()

        #--- livestatus_broker.main
        self.livestatus_broker.log = logger
        # this seems to damage the logger so that the scheduler can't use it
        #self.livestatus_broker.log.load_obj(self.livestatus_broker)
        self.livestatus_broker.debug_output = []
        self.livestatus_broker.modules_manager = ModulesManager('livestatus', self.livestatus_broker.find_modules_path(), [])
        self.livestatus_broker.modules_manager.set_modules(self.livestatus_broker.modules)
        # We can now output some previouly silented debug ouput
        self.livestatus_broker.do_load_modules()
        for inst in self.livestatus_broker.modules_manager.instances:
            if inst.properties["type"].startswith('logstore'):
                f = getattr(inst, 'load', None)
                if f and callable(f):
                    f(self.livestatus_broker)  # !!! NOT self here !!!!
                break
        for s in self.livestatus_broker.debug_output:
            print "errors during load", s
        del self.livestatus_broker.debug_output
        self.livestatus_broker.rg = LiveStatusRegenerator()
        self.livestatus_broker.datamgr = datamgr
        datamgr.load(self.livestatus_broker.rg)
        self.livestatus_broker.query_cache = LiveStatusQueryCache()
        self.livestatus_broker.query_cache.disable()
        self.livestatus_broker.rg.register_cache(self.livestatus_broker.query_cache)
        #--- livestatus_broker.main

        self.livestatus_broker.init()
        self.livestatus_broker.db = self.livestatus_broker.modules_manager.instances[0]
        self.livestatus_broker.livestatus = LiveStatus(self.livestatus_broker.datamgr, self.livestatus_broker.query_cache, self.livestatus_broker.db, self.livestatus_broker.pnp_path, self.livestatus_broker.from_q)

        #--- livestatus_broker.do_main
        self.livestatus_broker.db.open()
        #--- livestatus_broker.do_main


# Hook for old python some test
if not hasattr(ShinkenTest, 'assertNotIn'):
    def assertNotIn(self, member, container, msg=None):
       self.assertTrue(member not in container)
    ShinkenTest.assertNotIn = assertNotIn
        

if not hasattr(ShinkenTest, 'assertIn'):
    def assertIn(self, member, container, msg=None):
        self.assertTrue(member in container)
    ShinkenTest.assertIn = assertIn
                   


if __name__ == '__main__':
    unittest.main()
