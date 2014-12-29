#!/usr/bin/env python
# Copyright (C) 2009-2014:
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
# This file is used to test acknowledge of problems
#

from shinken_test import *


class TestConfig(ShinkenTest):

    def setUp(self):
        self.setup_with_file('etc/shinken_commands_perfdata.cfg')

    def test_service_perfdata_command(self):
        self.print_header()

        # We want an eventhandelr (the perfdata command) to be put in the actions dict
        # after we got a service check
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        print "Service perfdata command", svc.__class__.perfdata_command, type(svc.__class__.perfdata_command)
        # We do not want to be just a string but a real command
        self.assertNotIsInstance(svc.__class__.perfdata_command, str)
        print svc.__class__.perfdata_command.__class__.my_type
        self.assertEqual('CommandCall', svc.__class__.perfdata_command.__class__.my_type)
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "Actions", self.sched.actions
        self.assertEqual(1, self.count_actions())

        # Ok now I disable the perfdata
        now = time.time()
        cmd = "[%lu] DISABLE_PERFORMANCE_DATA" % now
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [[svc, 0, 'OK | bibi=99%']])
        print "Actions", self.sched.actions
        self.assertEqual(0, self.count_actions())

    def test_host_perfdata_command(self):
        # We want an eventhandelr (the perfdata command) to be put in the actions dict
        # after we got a service check
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        print "Host perfdata command", host.__class__.perfdata_command, type(host.__class__.perfdata_command)
        # We do not want to be just a string but a real command
        self.assertNotIsInstance(host.__class__.perfdata_command, str)
        print host.__class__.perfdata_command.__class__.my_type
        self.assertEqual('CommandCall', host.__class__.perfdata_command.__class__.my_type)
        self.scheduler_loop(1, [[host, 0, 'UP | bibi=99%']])
        print "Actions", self.sched.actions
        self.assertEqual(1, self.count_actions())

        # Ok now I disable the perfdata
        now = time.time()
        cmd = "[%lu] DISABLE_PERFORMANCE_DATA" % now
        self.sched.run_external_command(cmd)
        self.scheduler_loop(1, [[host, 0, 'UP | bibi=99%']])
        print "Actions", self.sched.actions
        self.assertEqual(0, self.count_actions())

    def test_multiline_perfdata(self):
        self.print_header()

        # We want an eventhandelr (the perfdata command) to be put in the actions dict
        # after we got a service check
        now = time.time()
        host = self.sched.hosts.find_by_name("test_host_0")
        host.checks_in_progress = []
        host.act_depend_of = []  # ignore the router
        svc = self.sched.services.find_srv_by_name_and_hostname("test_host_0", "test_ok_0")
        svc.checks_in_progress = []
        svc.act_depend_of = []  # no hostchecks on critical checkresults
        #--------------------------------------------------------------
        # initialize host/service state
        #--------------------------------------------------------------
        print "Service perfdata command", svc.__class__.perfdata_command, type(svc.__class__.perfdata_command)
        # We do not want to be just a string but a real command
        self.assertNotIsInstance(svc.__class__.perfdata_command, str)
        print svc.__class__.perfdata_command.__class__.my_type
        self.assertEqual('CommandCall', svc.__class__.perfdata_command.__class__.my_type)
        output = """DISK OK - free space: / 3326 MB (56%); | /=2643MB;5948;5958;0;5968
/ 15272 MB (77%);
/boot 68 MB (69%);
/home 69357 MB (27%);
/var/log 819 MB (84%); | /boot=68MB;88;93;0;98
/home=69357MB;253404;253409;0;253414
/var/log=818MB;970;975;0;980
        """
        self.scheduler_loop(1, [[svc, 0, output]])
        print "Actions", self.sched.actions
        print 'Output', svc.output
        print 'long', svc.long_output
        print 'perf', svc.perf_data

        self.assertEqual('DISK OK - free space: / 3326 MB (56%);', svc.output.strip())
        self.assertEqual(u'/=2643MB;5948;5958;0;5968 /boot=68MB;88;93;0;98 /home=69357MB;253404;253409;0;253414 /var/log=818MB;970;975;0;980', svc.perf_data.strip())
        print svc.long_output.split('\n')
        self.assertEqual(u"""/ 15272 MB (77%);
/boot 68 MB (69%);
/home 69357 MB (27%);
/var/log 819 MB (84%);""", svc.long_output)



if __name__ == '__main__':
    unittest.main()
