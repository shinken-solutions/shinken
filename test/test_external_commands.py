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
# This file is used to test reading and processing of config files
#

from shinken_test import *
from shinken.external_command import ExternalCommandManager
import os
import cPickle


class TestConfig(ShinkenTest):
    # setUp is inherited from ShinkenTest

    def send_cmd(self, line):
        s = '[%d] %s\n' % (int(time.time()), line)
        print "Writing %s in %s" % (s, self.conf.command_file)
        fd = open(self.conf.command_file, 'wb')
        fd.write(s)
        fd.close()

    def test_external_comand(self):
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        router = self.sched.hosts.find_by_name("test_router_0")
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [svc, 2, 'BAD | value1=0 value2=0']])
        self.assert_(host.state == 'UP')
        self.assert_(host.state_type == 'HARD')

        excmd = '[%d] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Bob is not happy' % time.time()
        self.sched.run_external_command(excmd)
        self.scheduler_loop(1, [])
        self.scheduler_loop(1, [])  # Need 2 run for get then consume)
        self.assert_(host.state == 'DOWN')
        self.assert_(host.output == 'Bob is not happy')

        # Now with performance data
        excmd = '[%d] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Bob is not happy|rtt=9999' % time.time()
        self.sched.run_external_command(excmd)
        self.scheduler_loop(1, [])
        self.scheduler_loop(1, [])  # Need 2 run for get then consume)
        self.assert_(host.state == 'DOWN')
        self.assert_(host.output == 'Bob is not happy')
        self.assert_(host.perf_data == 'rtt=9999')

        # Now with full-blown performance data. Here we have to watch out:
        # Is a ";" a separator for the external command or is it
        # part of the performance data?
        excmd = '[%d] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Bob is not happy|rtt=9999;5;10;0;10000' % time.time()
        self.sched.run_external_command(excmd)
        self.scheduler_loop(1, [])
        self.scheduler_loop(1, [])  # Need 2 run for get then consume)
        self.assert_(host.state == 'DOWN')
        self.assert_(host.output == 'Bob is not happy')
        print "perf (%s)" % host.perf_data
        self.assert_(host.perf_data == 'rtt=9999;5;10;0;10000')

        # The same with a service
        excmd = '[%d] PROCESS_SERVICE_CHECK_RESULT;test_host_0;test_ok_0;1;Bobby is not happy|rtt=9999;5;10;0;10000' % time.time()
        self.sched.run_external_command(excmd)
        self.scheduler_loop(1, [])
        self.scheduler_loop(1, [])  # Need 2 run for get then consume)
        self.assert_(svc.state == 'WARNING')
        self.assert_(svc.output == 'Bobby is not happy')
        print "perf (%s)" % svc.perf_data
        self.assert_(svc.perf_data == 'rtt=9999;5;10;0;10000')

        # Clean the command_file
        #try:
        #    os.unlink(self.conf.command_file)
        #except:
        #    pass


        # Now with PAST DATA. We take the router because it was not called from now.
        past = int(time.time() - 30)
        excmd = '[%d] PROCESS_HOST_CHECK_RESULT;test_router_0;2;Bob is not happy|rtt=9999;5;10;0;10000' % past
        self.sched.run_external_command(excmd)
        self.scheduler_loop(1, [])
        self.scheduler_loop(1, [])  # Need 2 run for get then consume)
        self.assert_(router.state == 'DOWN')
        self.assert_(router.output == 'Bob is not happy')
        print "perf (%s)" % router.perf_data
        self.assert_(router.perf_data == 'rtt=9999;5;10;0;10000')
        print "Is the last check agree?", past, router.last_chk
        self.assert_(past == router.last_chk)

        # Now an even earlier check, should NOT be take
        very_past = int(time.time() - 3600)
        excmd = '[%d] PROCESS_HOST_CHECK_RESULT;test_router_0;2;Bob is not happy|rtt=9999;5;10;0;10000' % very_past
        self.sched.run_external_command(excmd)
        self.scheduler_loop(1, [])
        self.scheduler_loop(1, [])  # Need 2 run for get then consume)
        self.assert_(router.state == 'DOWN')
        self.assert_(router.output == 'Bob is not happy')
        print "perf (%s)" % router.perf_data
        self.assert_(router.perf_data == 'rtt=9999;5;10;0;10000')
        print "Is the last check agree?", very_past, router.last_chk
        self.assert_(past == router.last_chk)

        # Now with crappy characters, like é
        host = self.sched.hosts.find_by_name("test_router_0")
        excmd = '[%d] PROCESS_HOST_CHECK_RESULT;test_router_0;2;Bob got a crappy character  é   and so is not not happy|rtt=9999' % int(time.time())
        self.sched.run_external_command(excmd)
        self.scheduler_loop(2, [])
        self.assert_(host.state == 'DOWN')
        self.assert_(host.output == u'Bob got a crappy character  é   and so is not not happy')
        self.assert_(host.perf_data == 'rtt=9999')

    def test_unknown_check_result_command(self):
        self.sched.conf.accept_passive_unknown_check_results = True

        # Sched receives known host but unknown service service_check_result
        self.sched.broks.clear()
        excmd = '[%d] PROCESS_SERVICE_CHECK_RESULT;test_host_0;unknownservice;1;Bobby is not happy|rtt=9999;5;10;0;10000' % time.time()
        self.sched.run_external_command(excmd)
        broks = [b for b in self.sched.broks.values() if b.type == 'unknown_service_check_result']
        self.assertTrue(len(broks) == 1)

        # Sched receives unknown host and service service_check_result
        self.sched.broks.clear()
        excmd = '[%d] PROCESS_SERVICE_CHECK_RESULT;unknownhost;unknownservice;1;Bobby is not happy|rtt=9999;5;10;0;10000' % time.time()
        self.sched.run_external_command(excmd)
        broks = [b for b in self.sched.broks.values() if b.type == 'unknown_service_check_result']
        self.assertTrue(len(broks) == 1)

        # Sched receives unknown host host_check_result
        self.sched.broks.clear()
        excmd = '[%d] PROCESS_HOST_CHECK_RESULT;unknownhost;1;Bobby is not happy|rtt=9999;5;10;0;10000' % time.time()
        self.sched.run_external_command(excmd)
        broks = [b for b in self.sched.broks.values() if b.type == 'unknown_host_check_result']
        self.assertTrue(len(broks) == 1)

        # Now turn it off...
        self.sched.conf.accept_passive_unknown_check_results = False

        # Sched receives known host but unknown service service_check_result
        self.sched.broks.clear()
        excmd = '[%d] PROCESS_SERVICE_CHECK_RESULT;test_host_0;unknownservice;1;Bobby is not happy|rtt=9999;5;10;0;10000' % time.time()
        self.sched.run_external_command(excmd)
        broks = [b for b in self.sched.broks.values() if b.type == 'unknown_service_check_result']
        self.assertTrue(len(broks) == 0)
        log_found = self.log_match(1, 'A command was received for service .* on host .*, but the service could not be found!')
        self.clear_logs()
        self.assertTrue(log_found)

    def test_unknown_check_result_brok(self):
        # unknown_host_check_result_brok
        excmd = '[1234567890] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Bob is not happy'
        expected = {'time_stamp': '1234567890', 'return_code': '2', 'host_name': 'test_host_0', 'output': 'Bob is not happy', 'perf_data': None}
        result = cPickle.loads(ExternalCommandManager.get_unknown_check_result_brok(excmd).data)
        self.assertEqual(expected, result)

        # unknown_host_check_result_brok with perfdata
        excmd = '[1234567890] PROCESS_HOST_CHECK_RESULT;test_host_0;2;Bob is not happy|rtt=9999'
        expected = {'time_stamp': '1234567890', 'return_code': '2', 'host_name': 'test_host_0', 'output': 'Bob is not happy', 'perf_data': 'rtt=9999'}
        result = cPickle.loads(ExternalCommandManager.get_unknown_check_result_brok(excmd).data)
        self.assertEqual(expected, result)

        # unknown_service_check_result_brok
        excmd = '[1234567890] PROCESS_HOST_CHECK_RESULT;host-checked;0;Everything OK'
        expected = {'time_stamp': '1234567890', 'return_code': '0', 'host_name': 'host-checked', 'output': 'Everything OK', 'perf_data': None}
        result = cPickle.loads(ExternalCommandManager.get_unknown_check_result_brok(excmd).data)
        self.assertEqual(expected, result)

        # unknown_service_check_result_brok with perfdata
        excmd = '[1234567890] PROCESS_SERVICE_CHECK_RESULT;test_host_0;test_ok_0;1;Bobby is not happy|rtt=9999;5;10;0;10000'
        expected = {'host_name': 'test_host_0', 'time_stamp': '1234567890', 'service_description': 'test_ok_0', 'return_code': '1', 'output': 'Bobby is not happy', 'perf_data': 'rtt=9999;5;10;0;10000'}
        result = cPickle.loads(ExternalCommandManager.get_unknown_check_result_brok(excmd).data)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
