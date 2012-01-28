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
        #--- livestatus_broker.main

        self.livestatus_broker.init()
        for i in self.livestatus_broker.modules_manager.instances:
            print "instance", i
        self.livestatus_broker.db = self.livestatus_broker.modules_manager.instances[0]
        self.livestatus_broker.livestatus = LiveStatus(self.livestatus_broker.datamgr, self.livestatus_broker.db, self.livestatus_broker.pnp_path, self.livestatus_broker.from_q)

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
            #'mongodb_uri' : "mongodb://127.0.0.1:27017",
            'mongodb_uri' : "mongodb://10.0.12.50:27017",
            'replica_set' : 'livestatus',
            'max_logs_age' : '14',
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
        #--- livestatus_broker.main

        self.livestatus_broker.init()
        self.livestatus_broker.db = self.livestatus_broker.modules_manager.instances[0]
        self.livestatus_broker.livestatus = LiveStatus(self.livestatus_broker.datamgr, self.livestatus_broker.db, self.livestatus_broker.pnp_path, self.livestatus_broker.from_q)

        #--- livestatus_broker.do_main
        self.livestatus_broker.db.open()
        #--- livestatus_broker.do_main

    def count_log_broks(self):
        return len([brok for brok in self.sched.broks.values() if brok.type == 'log'])


    def test_a_long_history(self):
        if not has_pymongo:
            return
        test_host_005 = self.sched.hosts.find_by_name("test_host_005")
        test_host_099 = self.sched.hosts.find_by_name("test_host_099")
        test_ok_00 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_00")
        test_ok_01 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_01")
        test_ok_04 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_04")
        test_ok_16 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_16")
        test_ok_99 = self.sched.services.find_srv_by_name_and_hostname("test_host_099", "test_ok_01")
        starttime = time.time()

        num_log_broks = 0
        try:
            numlogs = self.livestatus_broker.db.conn.bigbigbig.find().count()
        except Exception:
            numlogs = 0
        if numlogs == 0:
            # run silently
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            self.scheduler_loop(2, [
                [test_ok_00, 0, "OK"],
                [test_ok_01, 0, "OK"],
                [test_ok_04, 0, "OK"],
                [test_ok_16, 0, "OK"],
                [test_ok_99, 0, "OK"],
            ])
            num_log_broks += self.count_log_broks()
            self.update_broker()
            should_be = 0
            should_be_huhu = 0
            huhuhus = []
            #for i in xrange(3600 * 24 * 7):
            for i in xrange(10000): 
                if i % 1000 == 0:
                    sys.stderr.write("loop "+str(i))
                if i % 399 == 0:
                    self.scheduler_loop(3, [
                        [test_ok_00, 1, "WARN"],
                        [test_ok_01, 2, "CRIT"],
                        [test_ok_04, 3, "UNKN"],
                        [test_ok_16, 1, "WARN"],
                        [test_ok_99, 2, "HUHU"+str(i)],
                    ])
                    should_be += 3
                    should_be_huhu += 3
                    huhuhus.append(i)
                time.sleep(62)
                if i % 399 == 0:
                    self.scheduler_loop(1, [
                        [test_ok_00, 0, "OK"],
                        [test_ok_01, 0, "OK"],
                        [test_ok_04, 0, "OK"],
                        [test_ok_16, 0, "OK"],
                        [test_ok_99, 0, "OK"],
                    ])
                    should_be += 1
                time.sleep(2)
                if i % 199 == 0:
                    self.scheduler_loop(3, [
                        [test_ok_00, 1, "WARN"],
                        [test_ok_01, 2, "CRIT"],
                    ])
                time.sleep(62)
                if i % 199 == 0:
                    self.scheduler_loop(1, [
                        [test_ok_00, 0, "OK"],
                        [test_ok_01, 0, "OK"],
                    ])
                time.sleep(2)
                if i % 299 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 2, "DOWN"],
                    ])
                if i % 19 == 0:
                    self.scheduler_loop(3, [
                        [test_host_099, 2, "DOWN"],
                    ])
                time.sleep(62)
                if i % 299 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 0, "UP"],
                    ])
                if i % 19 == 0:
                    self.scheduler_loop(3, [
                        [test_host_099, 0, "UP"],
                    ])
                time.sleep(2)
                num_log_broks += self.count_log_broks()
                self.update_broker()
                if i % 1000 == 0:
                    self.livestatus_broker.db.commit()
            endtime = time.time()
            sys.stdout.close()
            sys.stdout = old_stdout
            self.livestatus_broker.db.commit()
        else:
            should_be = numlogs
            starttime = int(time.time())
            endtime = 0
            for doc in self.livestatus_broker.db.conn.bigbigbig.logs.find():
                if doc['time'] < starttime:
                    starttime = doc['time']
                if doc['time'] > endtime:
                    endtime = doc['time']
            print "starttime, endtime", starttime, endtime
        
        # now we have a lot of events
        # find type = HOST ALERT for test_host_005
        q = int((endtime - starttime) / 8)
        starttime += q
        endtime -= q
        request = """GET log
Columns: class time type state host_name service_description plugin_output message options contact_name command_name state_type current_host_groups current_service_groups
Filter: time >= """ + str(int(starttime)) + """
Filter: time <= """ + str(int(endtime)) + """
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
Filter: plugin_output ~ HUHU
OutputFormat: json"""
        # switch back to realtime. we want to know how long it takes
        fake_time_time = time.time
        fake_time_sleep = time.sleep
        time.time = original_time_time
        time.sleep = original_time_sleep
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        print "number of all documents", self.livestatus_broker.db.conn.bigbigbig.logs.find().count()
        print "number of log broks sent", num_log_broks
        print "number of lines in the response", len(pyresponse)
        print "should be", should_be
        time.time = fake_time_time
        time.sleep = fake_time_sleep
        hosts = set([h[4] for h in pyresponse])
        services = set([h[5] for h in pyresponse])
        print "found hosts", hosts
        print "found services", services
        alldocs = [d for d in self.livestatus_broker.db.conn.bigbigbig.logs.find()]
        clientselected = [d for d in alldocs if (d['time'] >= int(starttime) and d['time'] <= int(endtime) and d['host_name'] == 'test_host_099' and d['service_description'] == 'test_ok_01' and 'HUHU' in d['plugin_output'])]
        print "clientselected", len(clientselected)
        self.assert_(len(pyresponse) == len(clientselected))

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
        print numlogs, sum(daycount[:14]), daycount[:14]
        self.assert_(numlogs == sum(daycount[:14]))


if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

