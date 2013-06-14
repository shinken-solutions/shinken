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
# This file is used to test the npcd broker module
#

import os, sys, string, time
from multiprocessing import Queue

from shinken_test import unittest, ShinkenTest

from shinken.objects.module import Module
from shinken.modulesctx import modulesctx
npcdmod_broker = modulesctx.get_module('npcdmod')
Npcd_broker = npcdmod_broker.Npcd_broker


sys.setcheckinterval(10000)

modconf = Module()
modconf.module_name = "ncpd"
modconf.module_type = npcdmod_broker.properties['type']
modconf.modules = []
modconf.properties = npcdmod_broker.properties.copy()


class TestNpcd(ShinkenTest):

    def add(self, b):
        self.broks[b.id] = b

    def fake_check(self, ref, exit_status, output="OK"):
        print "fake", ref
        now = time.time()
        ref.schedule()
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
            self.worker_loop()
            for ref in reflist:
                (obj, exit_status, output) = ref
                obj.checks_in_progress = []
            self.sched.update_downtimes_and_comments()
            #time.sleep(ref.retry_interval * 60 + 1)
            #time.sleep(60 + 1)

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
            a.exit_status = 0
            self.sched.put_results(a)
        #self.show_actions()
        #print "------------ worker loop end ----------------"

    def update_broker(self):
        self.sched.get_new_broks()
        ids = self.sched.brokers['Default-Broker']['broks'].keys()
        ids.sort()
        for i in ids:
            brok = self.sched.brokers['Default-Broker']['broks'][i]
            brok.prepare()
            self.npcdmod_broker.manage_brok(brok)
        self.sched.broks = {}


    def print_header(self):
        print "#" * 80 + "\n" + "#" + " " * 78 + "#"
        print "#" + string.center(self.id(), 78) + "#"
        print "#" + " " * 78 + "#\n" + "#" * 80 + "\n"

    def write_correct_config(self):
        file = open("npcd.cfg", "w")
        file.write("perfdata_file = /tmp/pfnerf")
        file.write("perfdata_spool_dir = /tmp/pnp4shinken/var/perfdata")
        file.write("perfdata_spool_filename=pferf")
        file.close()

    def write_incomplete_config(self):
        file = open("npcd.cfg", "w")
        file.write("perfdata_file = /tmp/pfnerf")
        file.write("perfdata_spool_filename=pferf")
        file.close()

    def test_write_perfdata_file(self):
        self.print_header()
        if os.path.exists("./perfdata"):
            os.unlink("./perfdata")

        self.npcdmod_broker = Npcd_broker(modconf, None, './perfdata', '.', 'perfdata-target', 15)
        self.npcdmod_broker.properties['to_queue'] = 0

        self.npcdmod_broker.init()
        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')

        print "got initial broks"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 2, 'BAD | value1=0 value2=0']])
        self.update_broker()
        self.assert_(os.path.exists("./perfdata"))
        if os.path.exists("./perfdata"):
            self.npcdmod_broker.logfile.close()
            os.unlink("./perfdata")

    def test_npcd_got_missing_conf(self):
        self.print_header()
        if os.path.exists("./perfdata"):
            os.unlink("./perfdata")

        self.npcdmod_broker = Npcd_broker(modconf, None, './perfdata', '.', 'perfdata-target', 15)
        self.npcdmod_broker.properties['to_queue'] = 0
        self.npcdmod_broker.from_q = Queue()

        self.npcdmod_broker.init()
        
        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')

        print "got initial broks"
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults

        # We are a bad guy, and we change the service name
        svc.service_description = "Unkown"
        # and we force it to raise an asking now
        self.npcdmod_broker.last_need_data_send = 0

        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 2, 'BAD | value1=0 value2=0']])
        self.update_broker()
        self.assert_(os.path.exists("./perfdata"))
        if os.path.exists("./perfdata"):
            self.npcdmod_broker.logfile.close()
            os.unlink("./perfdata")
        print "Len" * 20, self.npcdmod_broker.from_q.qsize()
        self.assert_(self.npcdmod_broker.from_q.qsize() == 1)
        self.npcdmod_broker.from_q.get()
        self.npcdmod_broker.from_q.close()


if __name__ == '__main__':
    import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="Thruk.profile" )
