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

from shinken_test import *
import os
import sys
import re
import subprocess
import shutil
import time
import random
import copy

sys.path.append('../shinken/modules')

from shinken.brok import Brok
from shinken.objects.timeperiod import Timeperiod
from shinken.objects.module import Module
from shinken.objects.service import Service
livestatus_broker = modulesctx.get_module('livestatus')
LiveStatus_broker = livestatus_broker.LiveStatus_broker
LiveStatus = livestatus_broker.LiveStatus
LiveStatusRegenerator = livestatus_broker.LiveStatusRegenerator
LiveStatusQueryCache = livestatus_broker.LiveStatusQueryCache
Logline = livestatus_broker.Logline
LiveStatusLogStoreSqlite = modulesctx.get_module('logstore_sqlite').LiveStatusLogStoreSqlite
#from shinken.modules.logstore_sqlite.module import LiveStatusLogStoreSqlite
#from shinken.modules.livestatus import module as livestatus_broker
#from shinken.modules.livestatus.module import LiveStatus_broker
#from shinken.modules.livestatus.livestatus import LiveStatus
#from shinken.modules.livestatus.livestatus_regenerator import LiveStatusRegenerator
#from shinken.modules.livestatus.livestatus_query_cache import LiveStatusQueryCache
#from shinken.modules.livestatus.mapping import Logline

from shinken.comment import Comment

sys.setcheckinterval(10000)


class TestConfig(ShinkenTest):
    def contains_line(self, text, pattern):
        regex = re.compile(pattern)
        for line in text.splitlines():
            if re.search(regex, line):
                return True
        return False

    def update_broker(self, dodeepcopy=False):
        # The brok should be manage in the good order
        ids = self.sched.brokers['Default-Broker']['broks'].keys()
        ids.sort()
        for brok_id in ids:
            brok = self.sched.brokers['Default-Broker']['broks'][brok_id]
            #print "Managing a brok type", brok.type, "of id", brok_id
            #if brok.type == 'update_service_status':
            #    print "Problem?", brok.data['is_problem']
            if dodeepcopy:
                brok = copy.deepcopy(brok)
            brok.prepare()
            self.livestatus_broker.manage_brok(brok)
        self.sched.brokers['Default-Broker']['broks'] = {}

    def tearDown(self):
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs + "-journal"):
            os.remove(self.livelogs + "-journal")
        if os.path.exists("tmp/archives"):
            for db in os.listdir("tmp/archives"):
                print "cleanup", db
                os.remove(os.path.join("tmp/archives", db))
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.livestatus_broker = None


class TestConfigSmall(TestConfig):
    def setUp(self):
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')
        Comment.id = 1
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()
        print "Cleaning old broks?"
        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')
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
        print "-------------------------------------------"
        print "Service.lsm_host_name", Service.lsm_host_name
        print "Logline.lsm_current_host_name", Logline.lsm_current_host_name
        print "-------------------------------------------"

        self.livestatus_broker.db.log_db_do_archive()
        print "request logs from", int(now - 3600), int(now + 3600)
        print "request logs from", time.asctime(time.localtime(int(now - 3600))), time.asctime(time.localtime(int(now + 3600)))
        request = """GET log
Filter: time >= """ + str(int(now - 3600)) + """
Filter: time <= """ + str(int(now + 3600)) + """
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        print "next next_log_db_rotate", time.asctime(time.localtime(self.livestatus_broker.db.next_log_db_rotate))
        result = self.livestatus_broker.db.log_db_historic_contents()
        for day in result:
            print "file is", day[0]
            print "start is", time.asctime(time.localtime(day[3]))
            print "stop  is", time.asctime(time.localtime(day[4]))
            print "archive is", day[2]
            print "handle is", day[1]
        print self.livestatus_broker.db.log_db_relevant_files(now - 3600, now + 3600)


    def test_num_logs(self):
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        now = time.time()
        time_hacker.time_warp(-1 * 3600 * 24 * 7)
        num_logs = 0
        while time.time() < now:
            host.state = 'DOWN'
            host.state_type = 'SOFT'
            host.attempt = 1
            host.output = "i am down"
            host.raise_alert_log_entry()
            num_logs += 1
            time.sleep(3600)
            host.state = 'UP'
            host.state_type = 'HARD'
            host.attempt = 1
            host.output = "i am up"
            host.raise_alert_log_entry()
            num_logs += 1
            time.sleep(3600)
        self.update_broker()

        self.livestatus_broker.db.log_db_do_archive()
        print "request logs from", int(now - 3600 * 24 * 5), int(now - 3600 * 24 * 3)
        print "request logs from", time.asctime(time.localtime(int(now - 3600 * 24 * 5))), time.asctime(time.localtime(int(now - 3600 * 24 * 3)))
        request = """GET log
Filter: time >= """ + str(int(now - 3600 * 24 * 5)) + """
Filter: time <= """ + str(int(now - 3600 * 24 * 3)) + """
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        print "next next_log_db_rotate", time.asctime(time.localtime(self.livestatus_broker.db.next_log_db_rotate))
        result = self.livestatus_broker.db.log_db_historic_contents()
        for day in result:
            print "file is", day[0]
            print "start is", time.asctime(time.localtime(day[3]))
            print "stop  is", time.asctime(time.localtime(day[4]))
            print "archive is", day[2]
            print "handle is", day[1]
        print self.livestatus_broker.db.log_db_relevant_files(now - 3 * 24 * 3600, now)

    def test_split_database(self):
        #
        # after daylight-saving time has begun or ended,
        # this test may fail for some days
        #
        #os.removedirs("var/archives")
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        save_now = time.time()
        today = datetime.datetime.fromtimestamp(time.time())
        today_noon = datetime.datetime(today.year, today.month, today.day, 12, 0, 0)
        today_morning = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        back2days_noon = today_noon - datetime.timedelta(days=2)
        back2days_morning = today_morning - datetime.timedelta(days=2)
        back4days_noon = today_noon - datetime.timedelta(days=4)
        back4days_morning = today_morning - datetime.timedelta(days=4)
        today_noon = int(time.mktime(today_noon.timetuple()))
        today_morning = int(time.mktime(today_morning.timetuple()))
        back2days_noon = int(time.mktime(back2days_noon.timetuple()))
        back2days_morning = int(time.mktime(back2days_morning.timetuple()))
        back4days_noon = int(time.mktime(back4days_noon.timetuple()))
        back4days_morning = int(time.mktime(back4days_morning.timetuple()))
        now = time.time()
        time_hacker.time_warp(-1 * (now - back4days_noon))
        now = time.time()
        print "4t is", time.asctime(time.localtime(int(now)))
        logs = 0
        for day in range(1, 5):
            print "day", day
            # at 12:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(3600)
            # at 13:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(36000)
            # at 23:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(3600)
            # at 00:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(43200)
        # day 1: 1 * (2 + 2 + 2)
        # day 2: 2 * (2 + 2 + 2) + 1 * 2 (from last loop)
        # day 3: 3 * (2 + 2 + 2) + 2 * 2 (from last loop)
        # day 4: 4 * (2 + 2 + 2) + 3 * 2 (from last loop)
        # today: 4 * 2 (from last loop)
        # 6 + 14 + 22 + 30  + 8 = 80
        now = time.time()
        print "0t is", time.asctime(time.localtime(int(now)))
        request = """GET log
OutputFormat: python
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        pyresponse = eval(response)
        # ignore these internal logs
        pyresponse = [l for l in pyresponse if l[1].strip() not in ["Warning", "Info", "Debug"]]
        print "Raw pyresponse", pyresponse
        print "pyresponse", len(pyresponse)
        print "expect", logs
        self.assert_(len(pyresponse) == logs)

        self.livestatus_broker.db.log_db_do_archive()
        self.assert_(os.path.exists("tmp/archives"))
        self.assert_(len([d for d in os.listdir("tmp/archives") if not d.endswith("journal")]) == 4)
        lengths = []
        for db in sorted([d for d in os.listdir("tmp/archives") if not d.endswith("journal")]):
            dbmodconf = Module({'module_name': 'LogStore',
                'module_type': 'logstore_sqlite',
                'use_aggressive_sql': '0',
                'database_file': "tmp/archives/" + db,
                'max_logs_age': '0',
            })
            tmpconn = LiveStatusLogStoreSqlite(dbmodconf)
            tmpconn.open()
            numlogs = tmpconn.execute("SELECT COUNT(*) FROM logs")
            lengths.append(numlogs[0][0])
            print "db entries", db, numlogs
            tmpconn.close()
        print "lengths is", lengths
        self.assert_(lengths == [6, 14, 22, 30])

        request = """GET log
Filter: time >= """ + str(int(back4days_morning)) + """
Filter: time <= """ + str(int(back2days_noon)) + """
OutputFormat: python
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 30)
        print "pyresponse", len(pyresponse)
        print "expect", logs

        self.livestatus_broker.db.log_db_do_archive()

        request = """GET log
Filter: time >= """ + str(int(back4days_morning)) + """
Filter: time <= """ + str(int(back2days_noon)) + """
OutputFormat: python
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 30)
        print "pyresponse", len(pyresponse)
        print "expect", logs

        self.livestatus_broker.db.log_db_do_archive()

        request = """GET log
Filter: time >= """ + str(int(back4days_morning)) + """
Filter: time <= """ + str(int(back2days_noon) - 1) + """
OutputFormat: python
Columns: time type options state host_name"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 24)
        print "pyresponse", len(pyresponse)
        print "expect", logs

        # now warp to the time when we entered this test
        time_hacker.time_warp(-1 * (time.time() - save_now))
        # and now start the same logging
        today = datetime.datetime.fromtimestamp(time.time())
        today_noon = datetime.datetime(today.year, today.month, today.day, 12, 0, 0)
        today_morning = datetime.datetime(today.year, today.month, today.day, 0, 0, 0)
        back2days_noon = today_noon - datetime.timedelta(days=2)
        back2days_morning = today_morning - datetime.timedelta(days=2)
        back4days_noon = today_noon - datetime.timedelta(days=4)
        back4days_morning = today_morning - datetime.timedelta(days=4)
        today_noon = int(time.mktime(today_noon.timetuple()))
        today_morning = int(time.mktime(today_morning.timetuple()))
        back2days_noon = int(time.mktime(back2days_noon.timetuple()))
        back2days_morning = int(time.mktime(back2days_morning.timetuple()))
        back4days_noon = int(time.mktime(back4days_noon.timetuple()))
        back4days_morning = int(time.mktime(back4days_morning.timetuple()))
        now = time.time()
        time_hacker.time_warp(-1 * (now - back4days_noon))
        now = time.time()
        time.sleep(5)
        print "4t is", time.asctime(time.localtime(int(now)))
        logs = 0
        for day in range(1, 5):
            print "day", day
            # at 12:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(3600)
            # at 13:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(36000)
            # at 23:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(3600)
            # at 00:00
            now = time.time()
            print "it is", time.asctime(time.localtime(int(now)))
            self.write_logs(host, day)
            logs += 2 * day
            time.sleep(43200)
        # day 1: 1 * (2 + 2 + 2)
        # day 2: 2 * (2 + 2 + 2) + 1 * 2 (from last loop)
        # day 3: 3 * (2 + 2 + 2) + 2 * 2 (from last loop)
        # day 4: 4 * (2 + 2 + 2) + 3 * 2 (from last loop)
        # today: 4 * 2 (from last loop)
        # 6 + 14 + 22 + 30  + 8 = 80
        self.livestatus_broker.db.log_db_do_archive()
        self.assert_(os.path.exists("tmp/archives"))
        self.assert_(len([d for d in os.listdir("tmp/archives") if not d.endswith("journal")]) == 4)
        lengths = []
        for db in sorted([d for d in os.listdir("tmp/archives") if not d.endswith("journal")]):
            dbmodconf = Module({'module_name': 'LogStore',
                'module_type': 'logstore_sqlite',
                'use_aggressive_sql': '0',
                'database_file': "tmp/archives/" + db,
                'max_logs_age': '0',
            })
            tmpconn = LiveStatusLogStoreSqlite(dbmodconf)
            tmpconn.open()
            numlogs = tmpconn.execute("SELECT COUNT(*) FROM logs")
            lengths.append(numlogs[0][0])
            print "db entries", db, numlogs
            tmpconn.close()
        print "lengths is", lengths
        self.assert_(lengths == [12, 28, 44, 60])

    def xtest_david_database(self):
        #os.removedirs("var/archives")
        self.print_header()
        lengths = []
        dbh = LiveStatusDb("tmp/livestatus.db", "tmp/archives", 3600)
        numlogs = dbh.execute("SELECT COUNT(*) FROM logs")
        lengths.append(numlogs[0][0])
        print "db main entries", numlogs
        dbh.close()
        start = time.time()
        os.system("date")
        dbh = LiveStatusDb("tmp/livestatus.db", "tmp/archives", 3600)
        dbh.log_db_do_archive()
        dbh.close()
        os.system("date")
        stop = time.time()
        for db in sorted(os.listdir("tmp/archives")):
            dbh = LiveStatusDb("tmp/archives/" + db, "tmp", 3600)
            numlogs = dbh.execute("SELECT COUNT(*) FROM logs")
            lengths.append(numlogs[0][0])
            print "db entries", db, numlogs
            dbh.close()
        print "lengths is", lengths

    def test_archives_path(self):
        #os.removedirs("var/archives")
        self.print_header()
        lengths = []
        database_file = "dotlivestatus.db"
        archives_path = os.path.join(os.path.dirname(database_file), 'archives')
        print "archive is", archives_path

    def test_sven(self):
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        now = time.time()
        num_logs = 0
        host.state = 'DOWN'
        host.state_type = 'SOFT'
        host.attempt = 1
        host.output = "i am down"
        host.raise_alert_log_entry()
        time.sleep(60)
        host.state = 'UP'
        host.state_type = 'HARD'
        host.attempt = 1
        host.output = "i am up"
        host.raise_alert_log_entry()
        time.sleep(60)
        self.show_logs()
        self.update_broker()
        self.livestatus_broker.db.log_db_do_archive()
        query_end = time.time() + 3600
        query_start = query_end - 3600 * 24 * 21
        request = """GET log
Columns: class time type state host_name service_description plugin_output message options contact_name command_name state_type current_host_groups current_service_groups
Filter: time >= """ + str(int(query_start)) + """
Filter: time <= """ + str(int(query_end)) + """
And: 2
Filter: host_name = test_host_0
Filter: type = HOST ALERT
Filter: options ~ ;HARD;
Filter: type = INITIAL HOST STATE
Filter: options ~ ;HARD;
Filter: type = CURRENT HOST STATE
Filter: options ~ ;HARD;
Filter: type = HOST DOWNTIME ALERT
Or: 7
And: 2
Filter: host_name = test_host_0
Filter: type = SERVICE ALERT
Filter: options ~ ;HARD;
Filter: type = INITIAL SERVICE STATE
Filter: options ~ ;HARD;
Filter: type = CURRENT SERVICE STATE
Filter: options ~ ;HARD;
Filter: type = SERVICE DOWNTIME ALERT
Or: 7
And: 2
Filter: class = 2
Filter: type ~~ TIMEPERIOD TRANSITION
Or: 4
OutputFormat: json
ResponseHeader: fixed16
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print request
        print response
        pyresponse = eval(response.splitlines()[1])
        pyresponse = [l for l in pyresponse if l[2].strip() not in ["Warning", "Info", "Debug"]]
        print pyresponse
        self.assert_(len(pyresponse) == 2)


class TestConfigBig(TestConfig):

    def setUp(self):
        start_setUp = time.time()
        self.setup_with_file('etc/nagios_5r_100h_2000s.cfg')
        Comment.id = 1
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()
        print "Cleaning old broks?"
        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')

        self.update_broker()
        print "************* Overall Setup:", time.time() - start_setUp
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("test_host_000")
        host.__class__.use_aggressive_host_checking = 1

    def test_a_long_history(self):
        #return
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
        time_hacker.time_warp(-1 * days * 86400)
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
        numlogs = self.livestatus_broker.db.execute("SELECT COUNT(*) FROM logs")
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
        time_hacker.set_real_time()

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
        print "got response with true instead of negate"
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
        # the numlogs above only counts records in the currently attached db
        numlogs = self.livestatus_broker.db.execute("SELECT COUNT(*) FROM logs WHERE time >= %d AND time <= %d" % (int(query_start), int(query_end)))
        print "numlogs is", numlogs
        time_hacker.set_my_time()



class TestConfigNoLogstore(TestConfig):

    def setUp(self):
        start_setUp = time.time()
        self.setup_with_file('etc/nagios_1r_1h_1s.cfg')
        Comment.id = 1
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()
        print "Cleaning old broks?"
        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')
        self.update_broker()
        print "************* Overall Setup:", time.time() - start_setUp
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host = self.sched.hosts.find_by_name("test_host_0")
        host.__class__.use_aggressive_host_checking = 1

    def tearDown(self):
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs + "-journal"):
            os.remove(self.livelogs + "-journal")
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.livestatus_broker = None

    def init_livestatus(self):
        self.livelogs = 'tmp/livelogs.db' + self.testid
        modconf = Module({'module_name': 'LiveStatus',
            'module_type': 'livestatus',
            'port': str(50000 + os.getpid()),
            'pnp_path': 'tmp/pnp4nagios_test' + self.testid,
            'host': '127.0.0.1',
            'socket': 'live',
            'name': 'test', #?
            'database_file': self.livelogs,
        })

        dbmodconf = Module({'module_name': 'LogStore',
            'module_type': 'logstore_sqlite',
            'use_aggressive_sql': "0",
            'database_file': self.livelogs,
            'archive_path': os.path.join(os.path.dirname(self.livelogs), 'archives'),
        })
        ####################################
        # !NOT! modconf.modules = [dbmodconf]
        ####################################
        self.livestatus_broker = LiveStatus_broker(modconf)
        self.livestatus_broker.create_queues()

        self.livestatus_broker.init()

        #--- livestatus_broker.main
        self.livestatus_broker.log = logger
        # this seems to damage the logger so that the scheduler can't use it
        #self.livestatus_broker.log.load_obj(self.livestatus_broker)
        self.livestatus_broker.debug_output = []
        self.livestatus_broker.modules_manager = ModulesManager('livestatus', modulesctx.get_modulesdir(), [])
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
        self.livestatus_broker.add_compatibility_sqlite_module()
        self.livestatus_broker.rg = LiveStatusRegenerator()
        self.livestatus_broker.datamgr = datamgr
        datamgr.load(self.livestatus_broker.rg)
        self.livestatus_broker.query_cache = LiveStatusQueryCache()
        self.livestatus_broker.query_cache.disable()
        self.livestatus_broker.rg.register_cache(self.livestatus_broker.query_cache)
        #--- livestatus_broker.main

        #--- livestatus_broker.do_main
        self.livestatus_broker.db = self.livestatus_broker.modules_manager.instances[0]
        self.livestatus_broker.db.open()
        #--- livestatus_broker.do_main

        #--- livestatus_broker.manage_lql_thread
        self.livestatus_broker.livestatus = LiveStatus(self.livestatus_broker.datamgr, self.livestatus_broker.query_cache, self.livestatus_broker.db, self.livestatus_broker.pnp_path, self.livestatus_broker.from_q)
        #--- livestatus_broker.manage_lql_thread

    def test_has_implicit_module(self):
        self.assert_(self.livestatus_broker.modules_manager.instances[0].properties['type'] == 'logstore_sqlite')
        self.assert_(self.livestatus_broker.modules_manager.instances[0].__class__.__name__ == 'LiveStatusLogStoreSqlite')
        self.assert_(self.livestatus_broker.db.database_file == self.livelogs)


if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )
