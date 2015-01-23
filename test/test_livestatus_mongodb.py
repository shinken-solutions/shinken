#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
# This file is used to test host- and service-downtimes.
#

#import pydevd
#pydevd.settrace('localhost', port=3333, stdoutToServer=True, stderrToServer=True)


import os
import sys
import re
import socket
import subprocess
import shutil
import time
import random
import copy


from shinken_test import unittest

try:
    import pymongo

    pymongo_import_err = ''
except ImportError as pymongo_import_err:
    pymongo = None
    pymongo_import_err = "Could not import pymongo : %s" % pymongo_import_err
else:
    from shinken.modules.logstore_mongodb import LiveStatusLogStoreMongoDB


from shinken.brok import Brok
from shinken.external_command import ExternalCommand


from shinken_test import time_hacker

from shinken.objects.module import Module
from shinken.objects.service import Service
from shinken.modules.livestatus_broker.mapping import Logline



from mock_livestatus import mock_livestatus_handle_request
from test_livestatus import LiveStatus_Template


sys.setcheckinterval(10000)


# temp path for mongod files :
# as you can see it's relative path, that'll be relative to where the test is launched,
# which should be in the Shinken test directory.
_mongo_tmp_path = "./tmp/mongo"
_mongo_db = os.path.join(_mongo_tmp_path, 'db')
_mongo_log = os.path.join(_mongo_tmp_path, 'log.txt')



@unittest.skipIf(not pymongo, pymongo_import_err)
@mock_livestatus_handle_request
class TestConfig(LiveStatus_Template):

    # NB
    # subclasses must define _setup_config_file

    # how much seconds give to mongod be fully started
    # == listening on its input socket/port.
    mongod_start_timeout = 60

    @classmethod
    def setUpClass(cls):
        if not pymongo:
            return
        os.system('/bin/rm -rf "%s"' % _mongo_tmp_path)
        os.makedirs(_mongo_db)
        print('Starting embedded mongo daemon..')
        port = cls.get_free_port()
        cls.mongo_db_uri = "mongodb://127.0.0.1:%s" % port
        mp = cls._mongo_proc = subprocess.Popen(
            (['/usr/bin/mongod', '--dbpath', _mongo_db, '--port', str(port), '--logpath', _mongo_log,  '--smallfiles']),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False
        )
        print('Giving it some secs to correctly start..')
        time_hacker.set_real_time()
        # mongo takes some time to startup as it creates freshly new database files
        # so we need a relatively big timeout:
        timeout = time.time() + cls.mongod_start_timeout
        while time.time() < timeout:
            time.sleep(1)
            mp.poll()
            if mp.returncode is not None:
                try:
                    mongolog = open(_mongo_log).read()
                except Exception as err:
                    mongolog = "Couldn't read log from mongo log file: %s" % err
                raise RuntimeError("Launched mongod but it's directly died: rc=%s stdout/err=%s ; monglog=%s" % (
                    mp.returncode, mp.stdout.read(), mongolog))

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            errno = sock.connect_ex(('127.0.0.1', port))
            if not errno:
                sock.close()
                break
        else:
            mp.kill()
            raise RuntimeError('could not connect to port %s : mongod failed to correctly start?' % port)
        time_hacker.set_my_time()

    @classmethod
    def tearDownClass(cls):
        if not pymongo:
            return
        mp = cls._mongo_proc
        mp.terminate()
        print('Waiting mongod server to exit ..')
        time_hacker.set_real_time()
        for _ in range(10):
            time.sleep(2)
            if mp.poll() is not None:
                break
        else:
            print("didn't exited after 10 secs ! killing it..")
            mp.kill()
        mp.wait()
        os.system('/bin/rm -rf "%s"' % _mongo_tmp_path)

    def setUp(self):
        self.testid = str(os.getpid() + random.randint(1, 1000))
        dbmodconf = Module({'module_name': 'LogStore',
            'module_type': 'logstore_mongodb',
            'mongodb_uri': self.mongo_db_uri,
            'database': 'testtest' + self.testid,
        })
        super(TestConfig, self).setUp(dbmodconf=dbmodconf)



    def add(self, b):
        # ho boy..
        if not (hasattr(self, 'sched') and 'Default-Broker' in self.sched.brokers):
            return
        if isinstance(b, Brok):
            self.sched.brokers['Default-Broker']['broks'][b.id] = b
            return
        if isinstance(b, ExternalCommand):
            self.sched.run_external_command(b.cmd_line)


@mock_livestatus_handle_request
class TestConfigSmall(TestConfig):

    _setup_config_file = 'etc/nagios_1r_1h_1s.cfg'
    _setup_raise_on_bad_config = False

    def test_one_log(self):
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        now = time.time()
        time_hacker.time_warp(-3600)
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
        print("-------------------------------------------")
        print("Service.lsm_host_name", Service.lsm_host_name)
        print("Logline.lsm_current_host_name", Logline.lsm_current_host_name)
        print("-------------------------------------------")

        print("request logs from", int(now - 3600), int(now + 3600))
        print("request logs from", time.asctime(time.localtime(int(now - 3600))), time.asctime(time.localtime(int(now + 3600))))
        request = """GET log
Filter: time >= """ + str(int(now - 3600)) + """
Filter: time <= """ + str(int(now + 3600)) + """
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print(response)
        name = 'testtest' + self.testid
        numlogs = self.livestatus_broker.db.conn[name].logs.find().count()
        print(numlogs)
        self.assertEqual(2, numlogs)
        curs = self.livestatus_broker.db.conn[name].logs.find()
        self.assertEqual('SOFT', curs[0]['state_type'])
        self.assertEqual('HARD', curs[1]['state_type'])


@mock_livestatus_handle_request
class TestConfigBig(TestConfig):

    _setup_config_file = 'etc/shinken_5r_100h_2000s.cfg'


    def count_log_broks(self):
        return len([brok for brok in self.sched.broks.values() if brok.type == 'log'])

    def test_a_long_history(self):
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
        print("now it is", time.ctime(etime))
        print("now it is", time.gmtime(etime))
        etime_midnight = (etime - (etime % 86400)) + time.altzone
        print("midnight was", time.ctime(etime_midnight))
        print("midnight was", time.gmtime(etime_midnight))
        query_start = etime_midnight - (days - 1) * 86400
        query_end = etime_midnight
        print("query_start", time.ctime(query_start))
        print("query_end ", time.ctime(query_end))

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
        time_hacker.time_warp(-1 * days * 86400)
        print("warp back to", time.ctime(time.time()))
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
                if i % 9 == 0:
                    self.scheduler_loop(3, [
                        [test_ok_00, 1, "WARN"],
                        [test_ok_01, 2, "CRIT"],
                    ])

                time.sleep(62)
                if i % 9 == 0:
                    self.scheduler_loop(1, [
                        [test_ok_00, 0, "OK"],
                        [test_ok_01, 0, "OK"],
                    ])
                time.sleep(2)
                if i % 9 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 2, "DOWN"],
                    ])
                if i % 2 == 0:
                    self.scheduler_loop(3, [
                        [test_host_099, 2, "DOWN"],
                    ])
                time.sleep(62)
                if i % 9 == 0:
                    self.scheduler_loop(3, [
                        [test_host_005, 0, "UP"],
                    ])
                if i % 2 == 0:
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
        name = 'testtest' + self.testid
        numlogs = self.livestatus_broker.db.conn[name].logs.find().count()
        print("numlogs is", numlogs)

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
        time_hacker.set_real_time()

        print(request)
        print("query 1 --------------------------------------------------")
        tic = time.time()
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        tac = time.time()
        pyresponse = eval(response)
        print(response)
        print("number of records with test_ok_01", len(pyresponse))
        self.assertEqual(should_be, len(pyresponse))

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
        print("number of records without test_ok_01", len(notpyresponse))

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
        print("all records", len(allpyresponse))
        self.assertEqual(len(allpyresponse), len(notpyresponse) + len(pyresponse))


        # Now a pure class check query
        request = """GET log
Filter: time >= """ + str(int(query_start)) + """
Filter: time <= """ + str(int(query_end)) + """
Filter: class = 1
OutputFormat: json"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        allpyresponse = eval(response)
        print("all records", len(allpyresponse))
        self.assertEqual(len(allpyresponse), len(notpyresponse) + len(pyresponse))

        # now delete too old entries from the database (> 14days)
        # that's the job of commit_and_rotate_log_db()


        numlogs = self.livestatus_broker.db.conn[name].logs.find().count()
        times = [x['time'] for x in self.livestatus_broker.db.conn[name].logs.find()]
        self.assert_(times != [])
        print("whole database", numlogs, min(times), max(times))
        numlogs = self.livestatus_broker.db.conn[name].logs.find({
            '$and': [
                {'time': {'$gt': min(times)}},
                {'time': {'$lte': max(times)}}
            ]}).count()
        now = max(times)
        daycount = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for day in xrange(25):
            one_day_earlier = now - 3600*24
            numlogs = self.livestatus_broker.db.conn[name].logs.find({
                '$and': [
                    {'time': {'$gt': one_day_earlier}},
                    {'time': {'$lte': now}}
                ]}).count()
            daycount[day] = numlogs
            print("day -%02d %d..%d - %d" % (day, one_day_earlier, now, numlogs))
            now = one_day_earlier
        self.livestatus_broker.db.commit_and_rotate_log_db()
        now = max(times)
        for day in xrange(25):
            one_day_earlier = now - 3600*24
            numlogs = self.livestatus_broker.db.conn[name].logs.find({
                '$and': [
                    {'time': {'$gt': one_day_earlier}},
                    {'time': {'$lte': now}}
                ]}).count()
            print("day -%02d %d..%d - %d" % (day, one_day_earlier, now, numlogs))
            now = one_day_earlier
        numlogs = self.livestatus_broker.db.conn[name].logs.find().count()
        # simply an estimation. the cleanup-routine in the mongodb logstore
        # cuts off the old data at midnight, but here in the test we have
        # only accuracy of a day.
        self.assert_(numlogs >= sum(daycount[:7]))
        self.assert_(numlogs <= sum(daycount[:8]))

        time_hacker.set_my_time()

    def test_max_logs_age(self):
        dbmodconf = Module({'module_name': 'LogStore',
            'module_type': 'logstore_mongodb',
            'database': 'bigbigbig',
            'mongodb_uri': self.mongo_db_uri,
            'max_logs_age': '7y',
        })

        print(dbmodconf.max_logs_age)
        livestatus_broker = LiveStatusLogStoreMongoDB(dbmodconf)
        self.assertEqual(7*365, livestatus_broker.max_logs_age)



if __name__ == '__main__':
    command = """unittest.main()"""
    unittest.main()
