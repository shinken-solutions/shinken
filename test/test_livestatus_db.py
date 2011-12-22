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

from shinken.brok import Brok
from shinken.objects.timeperiod import Timeperiod
from shinken.objects.module import Module
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




    def tearDown(self):
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs+"-journal"):
            os.remove(self.livelogs+"-journal")
        if os.path.exists(self.pnp4nagios):
            shutil.rmtree(self.pnp4nagios)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        to_del = [attr for attr in self.livestatus_broker.livestatus.__class__.out_map['Host'].keys() if attr.startswith('host_')]
        for attr in to_del:
            del self.livestatus_broker.livestatus.__class__.out_map['Host'][attr]
        self.livestatus_broker = None

        if os.path.exists("tmp/archives"):
            for db in os.listdir("tmp/archives"):
                os.remove(os.path.join("tmp/archives", db))


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


    def test_num_logs(self):
        self.print_header()
        host = self.sched.hosts.find_by_name("test_host_0")
        now = time.time()
        time_warp(-1 * 3600 * 24 * 7)
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
            host.output = "i am down"
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
        time_warp(-1 * (now - back4days_noon))
        now = time.time()
        print "4t is", time.asctime(time.localtime(int(now)))
        logs = 0
        for day in range(1,5):
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
        self.assert_(len(pyresponse) == logs)
        print "pyresponse", len(pyresponse)
        print "expect", logs

        self.livestatus_broker.db.log_db_do_archive()
        self.assert_(os.path.exists("tmp/archives"))
        self.assert_(len([d for d in os.listdir("tmp/archives") if not d.endswith("journal")]) == 4)
        lengths = []
        for db in sorted([d for d in os.listdir("tmp/archives") if not d.endswith("journal")]):
            dbh = LiveStatusDb("tmp/archives/" + db, "tmp", 3600)
            numlogs = dbh.execute("SELECT COUNT(*) FROM logs")
            lengths.append(numlogs[0][0])
            print "db entries", db, numlogs
            dbh.close()
        print "lengths is", lengths
        self.assert_(lengths == [6,14,22,30])

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
        time_warp(-1 * (time.time() - save_now))
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
        time_warp(-1 * (now - back4days_noon))
        now = time.time()
        time.sleep(5)
        print "4t is", time.asctime(time.localtime(int(now)))
        logs = 0
        for day in range(1,5):
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
            dbh = LiveStatusDb("tmp/archives/" + db, "tmp", 3600)
            numlogs = dbh.execute("SELECT COUNT(*) FROM logs")
            lengths.append(numlogs[0][0])
            print "db entries", db, numlogs
            dbh.close()
        print "lengths is", lengths
        self.assert_(lengths == [12,28,44,60])


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



class TestConfigBig(TestConfig):
    def setUp(self):
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
        #self.livelogs = 'tmp/livelogs.db' + self.testid
        self.livelogs = 'tmp/livelogs.db' + "wrumm"
        self.db_archives = os.path.join(os.path.dirname(self.livelogs), 'archives')
        self.pnp4nagios = 'tmp/pnp4nagios_test' + self.testid
        self.livestatus_broker = Livestatus_broker(livestatus_modconf, '127.0.0.1', str(50000 + os.getpid()), 'live', [], self.livelogs, self.db_archives, 365, self.pnp4nagios)
        self.livestatus_broker.create_queues()
        #self.livestatus_broker.properties = {
        #    'to_queue' : 0,
        #    'from_queue' : 0
        #
        #    }
        self.livestatus_broker.init()
        self.livestatus_broker.db = LiveStatusDb(self.livestatus_broker.database_file, self.livestatus_broker.archive_path, self.livestatus_broker.max_logs_age)

        self.livestatus_broker.livestatus = LiveStatus(self.livestatus_broker.configs, self.livestatus_broker.hosts, self.livestatus_broker.services, self.livestatus_broker.contacts, self.livestatus_broker.hostgroups, self.livestatus_broker.servicegroups, self.livestatus_broker.contactgroups, self.livestatus_broker.timeperiods, self.livestatus_broker.commands, self.livestatus_broker.schedulers, self.livestatus_broker.pollers, self.livestatus_broker.reactionners, self.livestatus_broker.brokers, self.livestatus_broker.db, self.livestatus_broker.use_aggressive_sql, self.livestatus_broker.pnp_path, self.livestatus_broker.from_q)



    def test_a_long_history(self):
        #return
        test_host_005 = self.sched.hosts.find_by_name("test_host_005")
        test_host_099 = self.sched.hosts.find_by_name("test_host_099")
        test_ok_00 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_00")
        test_ok_01 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_01")
        test_ok_04 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_04")
        test_ok_16 = self.sched.services.find_srv_by_name_and_hostname("test_host_005", "test_ok_16")
        test_ok_99 = self.sched.services.find_srv_by_name_and_hostname("test_host_099", "test_ok_01")
        starttime = time.time()
        numlogs = self.livestatus_broker.db.execute("SELECT COUNT(*) FROM logs")
        if numlogs[0][0] == 0:
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
            self.update_broker()
            should_be = 0
            #for i in xrange(3600 * 24 * 7):
            for i in xrange(10000): 
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
                    should_be += 3
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
                self.update_broker()
                if i % 1000 == 0:
                    self.livestatus_broker.db.commit()
            endtime = time.time()
            sys.stdout.close()
            sys.stdout = old_stdout
            self.livestatus_broker.db.commit()
        else:
            should_be = numlogs[0][0]
            xxx = self.livestatus_broker.db.execute("SELECT min(time), max(time) FROM logs")
            print xxx
            starttime, endtime = [self.livestatus_broker.db.execute("SELECT min(time), max(time) FROM logs")][0][0]
            
        
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
OutputFormat: json"""
        # switch back to realtime. we want to know how long it takes
        fake_time_time = time.time
        fake_time_sleep = time.sleep
        time.time = original_time_time
        time.sleep = original_time_sleep
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        print "number of records", len(pyresponse)
        print "should be", should_be
        numlogs = self.livestatus_broker.db.execute("SELECT min(time), max(time) FROM logs")
        print starttime, endtime, numlogs
        self.livestatus_broker.livestatus.use_aggressive_sql = True
        print "aggrosql", self.livestatus_broker.livestatus.use_aggressive_sql
        response2, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        self.assert_(response2 == response)
        print "aggrosql", self.livestatus_broker.livestatus.use_aggressive_sql
        response2, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        self.assert_(response2 == response)
        self.livestatus_broker.livestatus.use_aggressive_sql = False
        print "aggrosql", self.livestatus_broker.livestatus.use_aggressive_sql
        response2, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        self.assert_(response2 == response)
        print "aggrosql", self.livestatus_broker.livestatus.use_aggressive_sql
        response2, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        self.assert_(response2 == response)
        # back to fake time for the other tests can run faster
        time.time = fake_time_time
        time.sleep = fake_time_sleep


    def tearDown(self):
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livelogs+"-journal"):
            os.remove(self.livelogs+"-journal")
        if os.path.exists(self.pnp4nagios):
            shutil.rmtree(self.pnp4nagios)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        to_del = [attr for attr in self.livestatus_broker.livestatus.__class__.out_map['Host'].keys() if attr.startswith('host_')]
        for attr in to_del:
            del self.livestatus_broker.livestatus.__class__.out_map['Host'][attr]
        self.livestatus_broker = None



if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

