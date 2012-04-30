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

# we have an external process, so we must un-fake time functions
time.time = original_time_time
time.sleep = original_time_sleep



class TestConfig(ShinkenTest):
    def contains_line(self, text, pattern):
        regex = re.compile(pattern)
        for line in text.splitlines():
            if re.search(regex, line):
                return True
        return False


    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        super(TestConfig, self).scheduler_loop(count, reflist, do_sleep, sleep_time)
        if self.nagios_installed() and hasattr(self, 'nagios_started'):
            self.nagios_loop(1, reflist)
  

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


    def lines_equal(self, text1, text2):
        # gets two multiline strings and compares the contents
        # lifestatus output may not be in alphabetical order, so this
        # function is used to compare unordered output with unordered
        # expected output
        # sometimes mklivestatus returns 0 or 1 on an empty result
        text1 = text1.replace("200           1", "200           0")
        text2 = text2.replace("200           1", "200           0")
        text1 = text1.rstrip()
        text2 = text2.rstrip()
        #print "text1 //%s//" % text1
        #print "text2 //%s//" % text2
        sorted1 = "\n".join(sorted(text1.split("\n")))
        sorted2 = "\n".join(sorted(text2.split("\n")))
        len1 = len(text1.split("\n"))
        len2 = len(text2.split("\n"))
        #print "%s == %s text cmp %s" % (len1, len2, sorted1 == sorted2)
        #print "text1 //%s//" % sorted(text1.split("\n"))
        #print "text2 //%s//" % sorted(text2.split("\n"))
        if sorted1 == sorted2 and len1 == len2:
            return True
        else:
            # Maybe list members are different
            # allhosts;test_host_0;test_ok_0;servicegroup_02,servicegroup_01,ok
            # allhosts;test_host_0;test_ok_0;servicegroup_02,ok,servicegroup_01
            # break it up to
            # [['allhosts'], ['test_host_0'], ['test_ok_0'],
            #     ['ok', 'servicegroup_01', 'servicegroup_02']]
            [line for line in sorted(text1.split("\n"))]
            data1 = [[sorted(c.split(',')) for c in columns] for columns in [line.split(';') for line in sorted(text1.split("\n")) if line]]
            data2 = [[sorted(c.split(',')) for c in columns] for columns in [line.split(';') for line in sorted(text2.split("\n")) if line]]
            #print "text1 //%s//" % data1
            #print "text2 //%s//" % data2
            # cmp is clever enough to handle nested arrays 
            return cmp(data1, data2) == 0
            

    def show_broks(self, title):
        print
        print "--- ", title
        for brok in sorted(self.sched.broks.values(), lambda x, y: x.id - y.id):
            if re.compile('^service_').match(brok.type):
                print "BROK:", brok.type
                print "BROK   ", brok.data['in_checking']
        self.update_broker()
        request = 'GET services\nColumns: service_description is_executing\n'
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response


    def nagios_installed(self, path='/usr/local/nagios/bin/nagios', livestatus='/usr/local/nagios/lib/mk-livestatus/livestatus.o'):
        return False
        raise
        if os.path.exists(path) and os.access(path, os.X_OK) and os.path.exists(livestatus):
            self.nagios_path = path
            self.livestatus_path = livestatus
            return True
        else:
            return False


    # shinkenize_nagios_config('nagios_1r_1h_1s')
    # We assume that there is a nagios_1r_1h_1s.cfg and a nagios_1r_1h_1s directory for the objects
    def unshinkenize_config(self, configname):
        new_configname = configname + '_' + str(os.getpid())
        config = open('etc/nagios_' + configname + '.cfg')
        text = config.readlines()
        config.close()

        newconfig = open('etc/nagios_' + new_configname + '.cfg', 'w')
        for line in text:
            if re.search('^resource_file=', line):
                newconfig.write("resource_file=etc/resource.cfg\n")
            elif re.search('shinken\-specific\.cfg', line):
                pass
            elif re.search('enable_problem_impacts_states_change', line):
                pass
            elif re.search('cfg_dir=', line):
                newconfig.write(re.sub(configname, new_configname, line))
            elif re.search('cfg_file=', line):
                newconfig.write(re.sub(configname, new_configname, line))
            elif re.search('execute_host_checks=', line):
                newconfig.write("execute_host_checks=0\n")
            elif re.search('execute_service_checks=', line):
                newconfig.write("execute_service_checks=0\n")
            elif re.search('^debug_level=', line):
                newconfig.write("debug_level=0\n")
            elif re.search('^debug_verbosity=', line):
                newconfig.write("debug_verbosity=0\n")
            elif re.search('^status_update_interval=', line):
                newconfig.write("status_update_interval=30\n")
            elif re.search('^command_file=', line):
                newconfig.write("command_file=var/nagios.cmd\n")
            elif re.search('^command_check_interval=', line):
                newconfig.write("command_check_interval=1s\n")
            else:
                newconfig.write(line)
        newconfig.write('broker_module=/usr/local/nagios/lib/mk-livestatus/livestatus.o var/live' + "\n")
        newconfig.close()
        for dirfile in os.walk('etc/' + configname):
            dirpath, dirlist, filelist = dirfile
            newdirpath = re.sub(configname, new_configname, dirpath)
            os.mkdir(newdirpath)
            for file in [f for f in filelist if re.search('\.cfg$', f)]:
                config = open(dirpath + '/' + file)
                text = config.readlines()
                config.close()
                newconfig = open(newdirpath + '/' + file, 'w')
                for line in text:
                    if re.search('^\s*criticity', line):
                        pass
                    elif re.search('enable_problem_impacts_states_change', line):
                        pass
                    else:
                        newconfig.write(line)
                newconfig.close()
        return new_configname

    
    def start_nagios(self, config):
        if os.path.exists('var/spool/checkresults'):
            # Cleanup leftover checkresults
            shutil.rmtree('var/spool/checkresults')
        for dir in ['tmp', 'var/tmp', 'var/spool', 'var/spool/checkresults', 'var/archives']:
            if not os.path.exists(dir):
                os.mkdir(dir)
        self.nagios_config = self.unshinkenize_config(config)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.nagios_proc = subprocess.Popen([self.nagios_path, 'etc/nagios_' + self.nagios_config + '.cfg'], close_fds=True)
        self.nagios_started = time.time()
        time.sleep(2)


    def stop_nagios(self):
        if self.nagios_installed():
            print "i stop nagios!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            time.sleep(5)
            if hasattr(self, 'nagios_proc'):
                attempt = 1
                while self.nagios_proc.poll() is None and attempt < 4:
                    self.nagios_proc.terminate()
                    attempt += 1
                    time.sleep(1)
                if self.nagios_proc.poll() is None:
                    self.nagios_proc.kill()
                if os.path.exists('etc/' + self.nagios_config):
                    shutil.rmtree('etc/' + self.nagios_config)
                if os.path.exists('etc/nagios_' + self.nagios_config + '.cfg'):
                    os.remove('etc/nagios_' + self.nagios_config + '.cfg')


    def ask_nagios(self, request):
        if time.time() - self.nagios_started < 2:
            time.sleep(1)
        if not request.endswith("\n"):
            request = request + "\n"
        unixcat = subprocess.Popen([os.path.dirname(self.nagios_path) + '/' + 'unixcat', 'var/live'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        tic = time.clock()
        out, err = unixcat.communicate(request)
        tac = time.clock()
        print "mklivestatus duration %f" % (tac - tic)
        attempt = 1
        while unixcat.poll() is None and attempt < 4:
            unixcat.terminate()
            attempt += 1
            time.sleep(1)
        if unixcat.poll() is None:
            unixcat.kill()
        print "unixcat says", out
        return out
        
    
    def nagios_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        now = time.time()
        buffer = open('var/pipebuffer', 'w')
        for ref in reflist:
            (obj, exit_status, output) = ref
            if obj.my_type == 'service':
                cmd = "[%lu] PROCESS_SERVICE_CHECK_RESULT;%s;%s;%d;%s\n" % (now, obj.host_name, obj.service_description, exit_status, output)
                print cmd
                buffer.write(cmd)
            else:
                cmd = "[%lu] PROCESS_HOST_CHECK_RESULT;%s;%d;%s\n" % (now, obj.host_name, exit_status, output)
                buffer.write(cmd)
        buffer.close()
        print "open pipe", self.conf.command_file
        fifo = open('var/nagios.cmd', 'w')
        cmd = "[%lu] PROCESS_FILE;%s;0\n" % (now, 'var/pipebuffer')
        fifo.write(cmd)
        fifo.flush()
        fifo.close()
        time.sleep(5)


    def nagios_extcmd(self, cmd):
        fifo = open('var/nagios.cmd', 'w')
        fifo.write(cmd)
        fifo.flush()
        fifo.close()
        time.sleep(5)



class TestConfigSmall(TestConfig):
    def setUp(self):
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



    def tearDown(self):
        self.stop_nagios()
        self.livestatus_broker.db.commit()
        self.livestatus_broker.db.close()
        if os.path.exists(self.livelogs):
            os.remove(self.livelogs)
        if os.path.exists(self.livestatus_broker.pnp_path):
            shutil.rmtree(self.livestatus_broker.pnp_path)
        if os.path.exists('var/nagios.log'):
            os.remove('var/nagios.log')
        if os.path.exists('var/retention.dat'):
            os.remove('var/retention.dat')
        if os.path.exists('var/status.dat'):
            os.remove('var/status.dat')
        self.livestatus_broker = None



    def test_host_wait(self):
        self.print_header()
        if self.nagios_installed():
            self.start_nagios('1r_1h_1s')
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 2, 'BAD']])
        self.update_broker(True)
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."
        print "i updated the broker at", time.time()
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."

        #---------------------------------------------------------------
        # get only the host names and addresses
        #---------------------------------------------------------------
        request = """
GET hosts
Columns: name state address
ColumnHeaders: on
Filter: host_name = test_host_0
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        good_response = """name;state;address
test_host_0;0;127.0.0.1
"""
        self.assert_(isinstance(response, str))
        self.assert_(self.lines_equal(response, good_response))

        request = """
GET hosts
Columns: name state address last_check
ColumnHeaders: on
Filter: host_name = test_host_0
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response

        time.sleep(1)
        now = time.time()
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."
        print "i query with trigger at", now
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."

        request = """
COMMAND [%d] SCHEDULE_FORCED_HOST_CHECK;test_host_0;%d

GET hosts
WaitObject: test_host_0
WaitCondition: last_check >= %d
WaitTimeout: 10000
WaitTrigger: check
Columns: last_check state plugin_output
Filter: host_name = test_host_0
Localtime: %d
OutputFormat: python
KeepAlive: on
ResponseHeader: fixed16
ColumnHeaders: off
""" % (now, now, now, now)

        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print "response is", response
        self.assert_(isinstance(response, list))
        self.assert_('wait' in [q.my_type for q in response])
        self.assert_('query' in [q.my_type for q in response])

        # launch the query, which must return an empty result
        query = [q for q in response if q.my_type == "query"][0]
        wait = [q for q in response if q.my_type == "wait"][0]
        result = wait.condition_fulfilled()
        # not yet...the plugin must run first
        self.assert_(not result)

        #result = query.launch_query()
        #response = query.response
        #response.format_live_data(result, query.columns, query.aliases)
        #output, keepalive = response.respond()
        #print "output is", output

        time.sleep(1)
        # update the broker
        # wait....launch the wait
        # launch the query again, which must return a result
        self.scheduler_loop(3, [[host, 2, 'DOWN']])
        self.update_broker(True)

        result = wait.condition_fulfilled()
        # not yet...the plugin must run first
        self.assert_(not result)

        result = query.launch_query()
        response = query.response
        response.columnheaders = "on"
        print response
        response.format_live_data(result, query.columns, query.aliases)
        output, keepalive = response.respond()
        print "output of the wait is (%s)" % output
        self.assert_(output.strip())

    def test_multiple_externals(self):
        self.print_header()
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = [] # ignore the router
        router = self.sched.hosts.find_by_name("test_router_0")
        router.checks_in_progress = []
        router.act_depend_of = [] # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = [] # no hostchecks on critical checkresults
        self.scheduler_loop(2, [[host, 0, 'UP'], [router, 0, 'UP'], [svc, 2, 'BAD']])
        self.update_broker(True)
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."
        print "i updated the broker at", time.time()
        print ".#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#."

        #---------------------------------------------------------------
        # get only the host names and addresses
        #---------------------------------------------------------------
        request = """COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

COMMAND [1303425876] SCHEDULE_FORCED_HOST_CHECK;test_host_0;1303425870

"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        print response
        good_response = ""
        self.assert_(isinstance(response, str))
        self.assert_(self.lines_equal(response, good_response))





if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

