#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
# This file is used to test reading and processing of config files
#

from shinken_test import *



class TestStrangeCaracterInCommands(ShinkenTest):
    def setUp(self):
        self.setup_with_file('etc/shinken_strange_characters_commands.cfg')
        time_hacker.set_real_time()

    # Try to call check dummy with very strange caracters and co, see if it run or
    # failed badly
    def test_strange_characters_commands(self):
        if os.name == 'nt':
            return
        #
        # Config is not correct because of a wrong relative path
        # in the main config file
        #
        print "Get the hosts and services"
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
        #self.scheduler_loop(2, [[host, 0, 'UP | value1=1 value2=2'], [router, 0, 'UP | rtt=10'], [svc, 2, 'BAD | value1=0 value2=0']])
        #self.assertEqual('UP', host.state)
        #self.assertEqual('HARD', host.state_type)
        print svc.check_command
        self.assertEqual(0, len(svc.checks_in_progress))
        svc.launch_check(time.time())
        print svc.checks_in_progress
        self.assertEqual(1, len(svc.checks_in_progress))
        c = svc.checks_in_progress.pop()
        #print c
        c.execute()
        time.sleep(0.5)
        c.check_finished(8000)
        print c.status
        self.assertEqual('done', c.status)
        self.assertEqual('£°é§', c.output)
        print "Done with good output, that's great"
        svc.consume_result(c)
        self.assertEqual(unicode('£°é§'.decode('utf8')), svc.output)



if __name__ == '__main__':
    unittest.main()
