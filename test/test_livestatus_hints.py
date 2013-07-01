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


class PerfTest(ShinkenTest):

    def update_broker(self, dodeepcopy=False):
        # The brok should be manage in the good order
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


class TestConfigBig(PerfTest):
    def setUp(self):
        print "comment me for performance tests"
        self.setup_with_file('etc/nagios_10r_1000h_20000s.cfg')
        # ...test_router_09
        # ...test_host_0999
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()

        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')

        self.update_broker()
        self.nagios_path = None
        self.livestatus_path = None
        self.nagios_config = None
        self.adjust_object_prefixes()

    def adjust_object_prefixes(self):
        host = [h for h in self.sched.hosts if "host" in h.host_name][0]
        if host.host_name.startswith("test_"):
            self.host_prefix = "test_"
        else:
            self.host_prefix = ""
        service = [s for s in self.sched.services][0]
        if service.service_description.startswith("test_"):
            self.service_prefix = "test_"
        else:
            self.service_prefix = ""
        # add use_aggressive_host_checking so we can mix exit codes 1 and 2
        # but still get DOWN state
        host.__class__.use_aggressive_host_checking = 1
        self.services_per_host = len(self.sched.services) / len([h for h in self.sched.hosts if h.host_name.startswith(self.host_prefix+"host_")])
        hosts = len([h for h in self.sched.hosts if h.host_name.startswith(self.host_prefix+"host_")])
        if self.services_per_host > 10:
            self.service_format = "%sok_%%02d" % self.service_prefix
        else:
            self.service_format = "%sok_%%d" % self.service_prefix
        if hosts < 100:
            self.host_format = "%shost_%%02d" % self.host_prefix
        elif hosts < 1000:
            self.host_format = "%shost_%%03d" % self.host_prefix
        else:
            self.host_format = "%shost_%%04d" % self.host_prefix

    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        super(TestConfigBig, self).scheduler_loop(count, reflist, do_sleep, sleep_time)

    def test_check_hint_services(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout

        range = int(len(self.sched.hosts) / 10)

        known_services = [s.get_full_name() for s in self.sched.services]
        real_services = 0
        request = """
GET services
"""
        for i in xrange(range):
            request += """Filter: host_name = %s
Filter: service_description = %s
And: 2
""" % (self.host_format % i, self.service_format % 3)
            if (self.host_format % i) + '/' + (self.service_format % 3) in known_services:
                real_services += 1 
        request += """Or: %d
Columns: description display_name state host_alias host_address plugin_output notes last_check next_check state_type current_attempt max_check_attempts last_state_change last_hard_state_change perf_data scheduled_downtime_depth acknowledged host_acknowledged host_scheduled_downtime_depth has_been_checked host_name check_command
OutputFormat:json
KeepAlive: on
""" % range
#ResponseHeader: fixed16
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == real_services)
        request += """Filter: host_name !=
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == real_services)

    def test_check_hint_services_by_hosts(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout

        range = int(len(self.sched.hosts) / 10)
        request = """
GET services
"""
        for i in xrange(range):
            request += """Filter: host_name = %s
""" % (self.host_format % i,)
        request += """Or: %d
Columns: description display_name state host_alias host_address plugin_output notes last_check next_check state_type current_attempt max_check_attempts last_state_change last_hard_state_change perf_data scheduled_downtime_depth acknowledged host_acknowledged host_scheduled_downtime_depth has_been_checked host_name check_command
OutputFormat:json
KeepAlive: on
""" % range
#ResponseHeader: fixed16
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == range * self.services_per_host)

        request += """Filter: host_name !=
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == range * self.services_per_host)


    def test_check_hint_services_by_host(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout

        range = int(len(self.sched.hosts) / 2)
        request = """
GET services
"""
        request += """Filter: host_name = %s
""" % (self.host_format % range,)
        request += """Columns: description display_name state host_alias host_address plugin_output notes last_check next_check state_type current_attempt max_check_attempts last_state_change last_hard_state_change perf_data scheduled_downtime_depth acknowledged host_acknowledged host_scheduled_downtime_depth has_been_checked host_name check_command
OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == self.services_per_host)

        request += """Filter: host_name !=
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == self.services_per_host)


    def test_check_hint_hosts_by_host(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout

        range = int(len(self.sched.hosts) / 2)
        request = """
GET hosts
"""
        request += """Filter: host_name = %s
""" % (self.host_format % range,)
        request += """OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 1)

        request += """Filter: host_name !=
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 1)

    def test_check_hint_services_by_hostgroup(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout

        request = """GET services
Filter: host_groups >= test
"""
        request += """Columns: description display_name state host_alias host_address plugin_output notes last_check next_check state_type current_attempt max_check_attempts last_state_change last_hard_state_change perf_data scheduled_downtime_depth acknowledged host_acknowledged host_scheduled_downtime_depth has_been_checked host_name check_command
OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        print len(pyresponse)
        self.assert_(len(pyresponse) == 2 * self.services_per_host)

        request += """Filter: host_name !=
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        print len(pyresponse)
        self.assert_(len(pyresponse) == 2 * self.services_per_host)

    def test_check_hint_hosts_by_hostgroup(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout

        range = int(len(self.sched.hosts) / 10)
        request = """GET hosts
Filter: host_groups >= test
OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 2)

        request += """Filter: host_name !=
"""
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 2)


    def test_check_hint_servicesbyhostgroup(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout
        test = self.sched.hostgroups.find_by_name("test")
        allgroups = sum([len(h.hostgroups) for h in test.members])

        request = """GET servicesbyhostgroup
Filter: host_groups >= test
"""
        request += """Columns: description display_name state host_alias host_address plugin_output notes last_check next_check state_type current_attempt max_check_attempts last_state_change last_hard_state_change perf_data scheduled_downtime_depth acknowledged host_acknowledged host_scheduled_downtime_depth has_been_checked host_name check_command
OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == allgroups * self.services_per_host)

        request += """Filter: host_name !=
"""
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == allgroups * self.services_per_host)

    def test_check_hint_hostsbygroup(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout
        test = self.sched.hostgroups.find_by_name("test")
        allgroups = sum([len(h.hostgroups) for h in test.members])

        request = """GET hostsbygroup
Filter: host_groups >= test
OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == allgroups)

        request += """Filter: host_name !=
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == allgroups)

    def test_check_hint_services_by_servicegroup(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout

        request = """GET services
Filter: service_groups >= test
"""
        request += """Columns: description display_name state host_alias host_address plugin_output notes last_check next_check state_type current_attempt max_check_attempts last_state_change last_hard_state_change perf_data scheduled_downtime_depth acknowledged host_acknowledged host_scheduled_downtime_depth has_been_checked host_name check_command
OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 2)

        request += """Filter: service_description !=
"""
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == 2)

    def test_check_hint_servicesbygroup(self):
        self.print_header()
        now = time.time()
        objlist = []
        old_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")
        for host in self.sched.hosts:
            objlist.append([host, 0, 'UP'])
        for service in self.sched.services:
            objlist.append([service, 2, 'CRIT'])
        self.scheduler_loop(1, objlist)
        self.update_broker()
        sys.stdout.close()
        sys.stdout = old_stdout
        test = self.sched.servicegroups.find_by_name("test")
        allgroups = sum([len(h.servicegroups) for h in test.members])

        request = """GET servicesbygroup
Filter: groups >= test
"""
        request += """Columns: description display_name state host_alias host_address plugin_output notes last_check next_check state_type current_attempt max_check_attempts last_state_change last_hard_state_change perf_data scheduled_downtime_depth acknowledged host_acknowledged host_scheduled_downtime_depth has_been_checked host_name check_command
OutputFormat:json
KeepAlive: on
"""
#ResponseHeader: fixed16
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == allgroups)

        request += """Filter: service_description !=
"""
        print request
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        response, keepalive = self.livestatus_broker.livestatus.handle_request(request)
        pyresponse = eval(response)
        self.assert_(len(pyresponse) == allgroups)


"""TODO


GET servicesbygroup
Filter: groups >= servicegroup_05
Stats


"""

class TestConfigCrazy(TestConfigBig):
    def setUp(self):
        print "comment me for performance tests"
        self.setup_with_file('etc/nagios_50r_5000h_30000s.cfg')
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()

        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')
        self.update_broker()
        self.nagios_path = None
        self.livestatus_path = None
        self.nagios_config = None
        self.adjust_object_prefixes()

    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        super(TestConfigCrazy, self).scheduler_loop(count, reflist, do_sleep, sleep_time)


class TestConfigSmall(TestConfigBig):
    def setUp(self):
        print "comment me for performance tests"
        self.setup_with_file('etc/nagios_5r_100h_2000s.cfg')
        self.testid = str(os.getpid() + random.randint(1, 1000))
        self.init_livestatus()

        self.sched.conf.skip_initial_broks = False
        self.sched.brokers['Default-Broker'] = {'broks' : {}, 'has_full_broks' : False}
        self.sched.fill_initial_broks('Default-Broker')

        self.update_broker()
        self.nagios_path = None
        self.livestatus_path = None
        self.nagios_config = None
        self.adjust_object_prefixes()

    def scheduler_loop(self, count, reflist, do_sleep=False, sleep_time=61):
        super(TestConfigSmall, self).scheduler_loop(count, reflist, do_sleep, sleep_time)


if __name__ == '__main__':
    #import cProfile
    command = """unittest.main()"""
    unittest.main()
    #cProfile.runctx( command, globals(), locals(), filename="/tmp/livestatus.profile" )

    #allsuite = unittest.TestLoader.loadTestsFromModule(TestConfig)
    #unittest.TextTestRunner(verbosity=2).run(allsuite)
