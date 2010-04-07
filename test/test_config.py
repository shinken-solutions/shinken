#!/usr/bin/env python2.6

#
# This file is used to test reading and processing of config files
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
        self.config_files = ['etc/nagios_broken_1.cfg']
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


    def show_logs(self):
        for brok in sorted(self.broks.values(), lambda x, y: x.id - y.id):
            if brok.type == 'log':
                print "LOG:", brok.data['log']


    def test_conf_is_correct(self):
        #
        # Config is not correct because of a wrong relative path 
        # in the main config file
        #
        self.assert_(not self.conf.conf_is_correct)
        self.show_logs()


if __name__ == '__main__':
    unittest.main()

