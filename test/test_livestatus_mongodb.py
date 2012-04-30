#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-

#Copyright (C) 2009-2010 :
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#
#This file is part of Shinken.
#
#Shinken is free software: you can redistribute it and/or modify
#it under the terms of the GNU Affero General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#Shinken is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU Affero General Public License for more details.
#
#You should have received a copy of the GNU Affero General Public License
#along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


#
# This file is used to test host- and service-downtimes.
#

from shinken_test import *
import os
import sys
import re
import subprocess
import shutil
import time
import random
import copy
import unittest

from shinken.brok import Brok
from shinken.objects.timeperiod import Timeperiod
from shinken.objects.module import Module
from shinken.objects.service import Service
from shinken.modules.livestatus_broker.mapping import Logline
from shinken.modules.logstore_sqlite import LiveStatusLogStoreSqlite
from shinken.comment import Comment

try:
    import pymongo
    has_pymongo = True
except Exception:
    has_pymongo = False


sys.setcheckinterval(10000)


class TestConfig(ShinkenTest):

    def tearDown(self):
        if not has_pymongo:
            return
        self.shutdown_livestatus()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs+"-journal"):
            os.remove(self.livelogs+"-journal")
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        if os.path.exists("tmp/archives"):
            for db in os.listdir("tmp/archives"):
                os.remove(os.path.join("tmp/archives", db))
        self.livestatus_broker = None

    def init_livestatus(self):
        self.livelogs = 'tmp/livelogs.db' + self.testid
        modconf = Module({'module_name' : 'LiveStatus',
            'module_type': 'livestatus',
            'port': str(50000 + os.getpid()),
            'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
            'host': '127.0.0.1',
            'socket': 'live',
            'name': 'test', #?
        })

        dbmodconf = Module({'module_name' : 'LogStore',
            'module_type': 'logstore_mongodb',
            'mongodb_uri': "mongodb://127.0.0.1:27017",
            'database': 'testtest'+self.testid,
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
                    f(self.livestatus_broker) #!!! NOT self here !!!!
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
        for i in self.livestatus_broker.modules_manager.instances:
            print "instance", i
        self.livestatus_broker.db = self.livestatus_broker.modules_manager.instances[0]
        self.livestatus_broker.livestatus = LiveStatus(self.livestatus_broker.datamgr, self.livestatus_broker.query_cache, self.livestatus_broker.db, self.livestatus_broker.pnp_path, self.livestatus_broker.from_q)

        #--- livestatus_broker.do_main
        self.livestatus_broker.db.open()
        #--- livestatus_broker.do_main

    def shutdown_livestatus(self):
        print "drop database", self.livestatus_broker.db.database
        self.livestatus_broker.db.conn.drop_database(self.livestatus_broker.db.database)
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()

    def contains_line(self, text, pattern):
        regex = re.compile(pattern)
        for line in text.splitlines():
            if re.search(regex, line):
                return True
        return False


    def update_broker(self, dodeepcopy=False):
        #The brok should be manage in the good order
        ids = self.sched.broks.keys()
        ids.sort()
        for brok_id in ids:
            brok = self.sched.broks[brok_id]
            #print "Managing a brok type", brok.type, "of id", brok_id
            #if brok.type == 'update_service_status':
            #    print "Problem?", brok.data['is_problem']
            if dodeepcopy:
                brok = copy.deepcopy(brok)
            self.livestatus_broker.manage_brok(brok)
        self.sched.broks = {}



class TestConfigSmall(TestConfig):
    def setUp(self):
        if not has_pymongo:
            return
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')
        Comment.id = 1
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()
        print "Cleaning old broks?"
        self.sched.conf.skip_initial_broks = False
        self.sched.fill_initial_broks()
        self.update_broker()
        self.nagios_path = None
        self.livestatus_path = None
        self.nagios_config = None
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("test_host_0")
        host.__class__.use_aggressive_host_checking = 1


    def write_logs(self, host, loops=0):
        for loop in range(0, loops):
            host.state = 'DOWN'
            host.state_type = 'SOFT'
            host.attempt = 1
            host.output = "i am down"
            host.raise_alert_log_entry()
            host.state = 'UP'
            host.state_type = 'HARD'
            host.attempt = 1
            host.output = "i am down"
            host.raise_alert_log_entry()
            self.update_broker()


    def test_hostsbygroup(self):
        if not has_pymongo:
            return
        self.print_header()
        now = time.time()
        objlist = []
        print "-------------------------------------------"
        print "Service.lsm_host_name", Service.lsm_host_name
        print "Logline.lsm_current_host_name", Logline.lsm_current_host_name
        print "-------------------------------------------"
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 0, 'OK'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        request = """GET hostsbygroup
ColumnHeaders: on
Columns: host_name hostgroup_name
Filter: groups >= allhosts
OutputFormat: csv
KeepAlive: on
ResponseHeader: fixed16
"""

        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response

    def test_one_log(self):
        if not has_pymongo:
            return
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        now = time.time()
        time_warp(-3600)
        num_logs = 0
	host.state = 'DOWN'
	host.state_type = 'SOFT'
	host.attempt = 1
	host.output = "i am down"
	host.raise_alert_log_entry()
	time.sleep(3600)
	host.state = 'UP'
	host.state_type = 'HARD'
	host.attempt = 1
	host.output = "i am up"
	host.raise_alert_log_entry()
	time.sleep(3600)
        self.update_broker()
        print "-------------------------------------------"
        print "Service.lsm_host_name", Service.lsm_host_name
        print "Logline.lsm_current_host_name", Logline.lsm_current_host_name
        print "-------------------------------------------"

        print "request logs from", int(now - 3600), int(now + 3600)
        print "request logs from", time.asctime(time.localtime(int(now - 3600))), time.asctime(time.localtime(int(now + 3600)))
        request = """GET log
Filter: time >= """ + str(int(now - 3600)) + """
Filter: time <= """ + str(int(now + 3600)) + """
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
            


class TestConfigBig(TestConfig):
    def setUp(self):
        if not has_pymongo:
            return
        start_setUp = time.time()
        self.setup_with_file('etc/nagios_5r_100h_2000s.cfg')
        Comment.id = 1
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()
        print "Cleaning old broks?"
        self.sched.conf.skip_initial_broks = False
        self.sched.fill_initial_broks()
        self.update_broker()
        print "************* Overall Setup:", time.time() - start_setUp
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("test_host_000")
        host.__class__.use_aggressive_host_checking = 1


    def init_livestatus(self):
        self.livelogs = "bigbigbig"
        modconf = Module({'module_name' : 'LiveStatus',
            'module_type' : 'livestatus',
            'port' : str(50000 + os.getpid()),
            'pnp_path' : 'tmp/livestatus_broker.pnp_path_test' + self.testid,
            'host' : '127.0.0.1',
            'socket' : 'live',
            'name' : 'test', #?
        })

        dbmodconf = Module({'module_name' : 'LogStore',
            'module_type' : 'logstore_mongodb',
            'database' : 'bigbigbig',
            'mongodb_uri' : "mongodb://127.0.0.1:27017",
            #'mongodb_uri' : "mongodb://10.0.12.50:27017,10.0.12.51:27017",
        #    'replica_set' : 'livestatus',
            'max_logs_age' : '7',
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
                    f(self.livestatus_broker) #!!! NOT self here !!!!
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

    def count_log_broks(self):
        return len([brok for brok in self.sched.broks.values() if brok.type == 'log'])


    def test_a_long_history(self):
        if not has_pymongo:
            return
        # copied from test_livestatus_cache
        test_host_005 = self.sched.hosts.find_by_name("test_host_005")
        test_host_099 = self.sched.hosts.find_by_name("test_host_099")
        test_ok_00 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_00")
        test_ok_01 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_01")
        test_ok_04 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_04")
        test_ok_16 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_16")
        test_ok_99 = self.sched.services.find_srv_by_name_and_hostname("test_host_099", "test_ok_01")

        days = 4
        etime = time.time()
        print "now it is", time.ctime(etime)
        print "now it is", time.gmtime(etime)
        etime_midnight = (etime - (etime % 86400)) + time.altzone
        print "midnight was", time.ctime(etime_midnight)
        print "midnight was", time.gmtime(etime_midnight)
        query_start = etime_midnight - (days - 1) * 86400
        query_end = etime_midnight
        print "query_start", time.ctime(query_start)
        print "query_end ", time.ctime(query_end)

        # |----------|----------|----------|----------|----------|---x
        #                                                            etime
        #                                                        etime_midnight
        #             ---x------
        #                etime -  4 days
        #                       |---
        #                       query_start
        #
        #                ............................................
        #                events in the log database ranging till now
        #
        #                       |________________________________|
        #                       events which will be read from db
        #
        loops = int(86400 / 192)
        time_warp(-1 * days * 86400)
        print "warp back to", time.ctime(time.time())
        # run silently
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        should_be = 0
        for day in xrange(days):
            sys.stderr.write("day %d now it is %s i run %d loops\n" % (day, time.ctime(time.time()), loops))
            self.scheduler_loop(2, [
                [test_ok_00, 0, "OK"],
                [test_ok_01, 0, "OK"],
                [test_ok_04, 0, "OK"],
                [test_ok_16, 0, "OK"],
                [test_ok_99, 0, "OK"],
            ])
            self.update_broker()
            #for i in xrange(3600 * 24 * 7):
            for i in xrange(loops):
                if i % 10000 == 0:
                    sys.stderr.write(str(i))
                if i % 399 == 0:
                    self.scheduler_loop(3, [
                        [test_ok_00, 1, "WARN"],
                        [test_ok_01, 2, "CRIT"],
                        [test_ok_04, 3, "UNKN"],
                        [test_ok_16, 1, "WARN"],
                        [test_ok_99, 2, "CRIT"],
                    ])
                    if int(time.time()) >= query_start and int(time.time()) <= query_end:
                        should_be += 3
                        sys.stderr.write("now it should be %s\n" % should_be)
                time.sleep(62)
                if i % 399 == 0:
                    self.scheduler_loop(1, [
                        [test_ok_00, 0, "OK"],
                        [test_ok_01, 0, "OK"],
                        [test_ok_04, 0, "OK"],
                        [test_ok_16, 0, "OK"],
                        [test_ok_99, 0, "OK"],
                    ])
                    if int(time.time()) >= query_start and int(time.time()) <= query_end:
                        should_be += 1
                        sys.stderr.write("now it should be %s\n" % should_be)
                time.sleep(2)
                if i % 17 == 0:
                    self.scheduler_loop(3, [
                        [test_ok_00, 1, "WARN"],
                        [test_ok_01, 2, "CRIT"],
                    ])

                time.sleep(62)
                if i % 17 == 0:
                    self.scheduler_loop(1, [
                        [test_ok_00, 0, "OK"],
                        [test_ok_01, 0, "OK"],
                    ])
                time.sleep(2)
                if i % 14 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 2, "DOWN"],
                    ])
                if i % 12 == 0:
                    self.scheduler_loop(3, [
                        [test_host_099, 2, "DOWN"],
                    ])
                time.sleep(62)
                if i % 14 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 0, "UP"],
                    ])
                if i % 12 == 0:
                    self.scheduler_loop(3, [
                        [test_host_099, 0, "UP"],
                    ])
                time.sleep(2)
                self.update_broker()
                if i % 1000 == 0:
                    self.livestatus_broker.db.commit()
            endtime = time.time()
            self.livestatus_broker.db.commit()
            sys.stderr.write("day %d end it is %s\n" % (day, time.ctime(time.time())))
        sys.stdout.close()
        sys.stdout = old_stdout
        self.livestatus_broker.db.commit_and_rotate_log_db()
        numlogs = self.livestatus_broker.db.conn.bigbigbig.logs.find().count()
        print "numlogs is", numlogs

        # now we have a lot of events
        # find type = HOST ALERT for test_host_005
        request = """GET log
Columns: class time type state host_name service_description plugin_output message options contact_name command_name state_type current_host_groups current_service_groups
Filter: time >= """ + str(int(query_start)) + """
Filter: time <= """ + str(int(query_end)) + """
Filter: type = SERVICE ALERT
And: 1
Filter: type = HOST ALERT
And: 1
Filter: type = SERVICE FLAPPING ALERT
Filter: type = HOST FLAPPING ALERT
Filter: type = SERVICE DOWNTIME ALERT
Filter: type = HOST DOWNTIME ALERT
Filter: type ~ starting...
Filter: type ~ shutting down...
Or: 8
Filter: host_name = test_host_099
Filter: service_description = test_ok_01
And: 5
OutputFormat: json"""
        # switch back to realtime. we want to know how long it takes
        fake_time_time = time.time
        fake_time_sleep = time.sleep
        time.time = original_time_time
        time.sleep = original_time_sleep
        print request
        print "query 1 --------------------------------------------------"
        tic = time.time()
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        tac = time.time()
        pyresponse = eval(response)
        print "number of records with test_ok_01", len(pyresponse)
        self.assert_(len(pyresponse) == should_be)

        # and now test Negate:
        request = """GET log
Filter: time >= """ + str(int(query_start)) + """
Filter: time <= """ + str(int(query_end)) + """
Filter: type = SERVICE ALERT
And: 1
Filter: type = HOST ALERT
And: 1
Filter: type = SERVICE FLAPPING ALERT
Filter: type = HOST FLAPPING ALERT
Filter: type = SERVICE DOWNTIME ALERT
Filter: type = HOST DOWNTIME ALERT
Filter: type ~ starting...
Filter: type ~ shutting down...
Or: 8
Filter: host_name = test_host_099
Filter: service_description = test_ok_01
And: 2
Negate:
And: 2
OutputFormat: json"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        notpyresponse = eval(response)
        print "number of records without test_ok_01", len(notpyresponse)

        request = """GET log
Filter: time >= """ + str(int(query_start)) + """
Filter: time <= """ + str(int(query_end)) + """
Filter: type = SERVICE ALERT
And: 1
Filter: type = HOST ALERT
And: 1
Filter: type = SERVICE FLAPPING ALERT
Filter: type = HOST FLAPPING ALERT
Filter: type = SERVICE DOWNTIME ALERT
Filter: type = HOST DOWNTIME ALERT
Filter: type ~ starting...
Filter: type ~ shutting down...
Or: 8
OutputFormat: json"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        allpyresponse = eval(response)
        print "all records", len(allpyresponse)
        self.assert_(len(allpyresponse) == len(notpyresponse) + len(pyresponse))

        # now delete too old entries from the database (> 14days)
        # that's the job of commit_and_rotate_log_db()
        #
        numlogs = self.livestatus_broker.db.conn.bigbigbig.logs.find().count()
        times = [x['time'] for x in self.livestatus_broker.db.conn.bigbigbig.logs.find()]
        print "whole database", numlogs, min(times), max(times)
        numlogs = self.livestatus_broker.db.conn.bigbigbig.logs.find({
            '$and' : [
                {'time' : { '$gt' : min(times)} },
                {'time' : { '$lte' : max(times)} }
            ]}).count()
        now = max(times)
        daycount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for day in xrange(25):
            one_day_earlier = now - 3600*24
            numlogs = self.livestatus_broker.db.conn.bigbigbig.logs.find({
                '$and' : [
                    {'time' : { '$gt' : one_day_earlier} },
                    {'time' : { '$lte' : now} }
                ]}).count()
            daycount[day] = numlogs
            print "day -%02d %d..%d - %d" % (day, one_day_earlier, now, numlogs)
            now = one_day_earlier
        self.livestatus_broker.db.commit_and_rotate_log_db()
        now = max(times)
        for day in xrange(25):
            one_day_earlier = now - 3600*24
            numlogs = self.livestatus_broker.db.conn.bigbigbig.logs.find({
                '$and' : [
                    {'time' : { '$gt' : one_day_earlier} },
                    {'time' : { '$lte' : now} }
                ]}).count()
            print "day -%02d %d..%d - %d" % (day, one_day_earlier, now, numlogs)
            now = one_day_earlier
        numlogs = self.livestatus_broker.db.conn.bigbigbig.logs.find().count()
        # simply an estimation. the cleanup-routine in the mongodb logstore
        # cuts off the old data at midnight, but here in the test we have
        # only accuracy of a day.
        self.assert_(numlogs >= sum(daycount[:7]))
        self.assert_(numlogs <= sum(daycount[:8]))

        time.time = fake_time_time
        time.sleep = fake_time_sleep


if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

